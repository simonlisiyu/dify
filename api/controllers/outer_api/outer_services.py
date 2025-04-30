# [Starry] directory outer api
# __author__ "lisiyu"
# date 2024/11/30

import logging
import uuid

import jwt
from flask import Response, request
from flask_login import current_user
from flask_restful import Resource, marshal_with, reqparse
from werkzeug.exceptions import abort

import services
from controllers.common.errors import FilenameNotExistsError
from controllers.console.app.error import (
    ProviderModelCurrentlyNotSupportError,
    ProviderNotInitializeError,
    ProviderQuotaExceededError,
)
from core.errors.error import (
    ModelCurrentlyNotSupportError,
    ProviderTokenNotInitError,
    QuotaExceededError,
)
from core.model_manager import ModelManager
from core.model_runtime.entities.model_entities import ModelType
from core.model_runtime.errors.invoke import InvokeAuthorizationError
from extensions.ext_database import db
from fields.document_fields import (
    dataset_and_document_fields,
)
from models.account import Account
from services.account_service import TenantService
from services.dataset_service import DatasetService, DocumentService
from services.entities.knowledge_entities.knowledge_entities import KnowledgeConfig
from services.file_service import FileService

from ..console.error import (
    FileTooLargeError,
    NoFileUploadedError,
    TooManyFilesError,
    UnsupportedFileTypeError,
)

logger = logging.getLogger(__name__)

PREVIEW_WORDS_LIMIT = 3000
CLIENTS_TOKENS = {"haizhi": "haizhi", "client2": "test"}
CLIENT_SECRET = "haizhi_secret"


def uuid_str(value):
    try:
        return str(uuid.UUID(value))
    except ValueError:
        abort(400, message="Invalid UUID format in parent_id.")


class DatasetApi(Resource):

    # @marshal_with(file_fields)
    @marshal_with(dataset_and_document_fields)
    def post(self):
        file = request.files["file"]
        source = request.form.get("source")
        parser = reqparse.RequestParser()
        parser.add_argument("authorization", type=str, location="headers", required=True, help="Authorization header is required for authentication.")

        parser.add_argument('separator', type=str, location='form', required=True)
        parser.add_argument('embedding_model', type=str, location='form', required=True)
        parser.add_argument('embedding_model_provider', type=str, location='form', required=True)
        parser.add_argument('reranking_model_name', type=str, location='form', required=True)
        parser.add_argument('reranking_provider_name', type=str, location='form', required=True)
        parser.add_argument('dataset_id', type=str, location='form', required=True)
        parser.add_argument('tenant_id', type=str, location='form', required=True)
        parser.add_argument('account_id', type=str, location='form', required=True)
        args = parser.parse_args()

        separator = args["separator"]
        embedding_model = args["embedding_model"]
        embedding_model_provider = args["embedding_model_provider"]
        reranking_model_name = args["reranking_model_name"]
        reranking_provider_name = args["reranking_provider_name"]
        directory_id = args["directory_id"]
        tenant_id = args["tenant_id"]
        account_id = args["account_id"]

        indexing_technique = "high_quality"
        doc_form = "text_model"
        doc_language = "Chinese"

        if not validate_token(args['authorization'], CLIENT_SECRET, CLIENTS_TOKENS):
            return Response("Unauthorized", status=401)

        if "file" not in request.files:
            raise NoFileUploadedError()

        if len(request.files) > 1:
            raise TooManyFilesError()

        if not file.filename:
            raise FilenameNotExistsError

        if source not in ("datasets", None):
            source = None

        user = db.session.query(Account)\
            .filter(Account.id == account_id)\
            .first()
        try:
            upload_file = FileService.upload_file(
                filename=file.filename,
                content=file.read(),
                mimetype=file.mimetype,
                user=user,
                source=source,
            )
        except services.errors.file.FileTooLargeError as file_too_large_error:
            raise FileTooLargeError(file_too_large_error.description)
        except services.errors.file.UnsupportedFileTypeError:
            raise UnsupportedFileTypeError()

        data_source = {
            "type": "upload_file",
            "info_list": {
                "data_source_type": "upload_file",
                "file_info_list": {
                    "file_ids": [
                        # "b1e3e024-d021-472a-8c97-8d6b0c6a4a37"
                        upload_file.id
                    ]
                }
            }
        }

        process_rule = {
            "rules": {
                "pre_processing_rules": [
                    {
                        "id": "remove_extra_spaces",
                        "enabled": True
                    },
                    {
                        "id": "remove_urls_emails",
                        "enabled": False
                    }
                ],
                "segmentation": {
                    # "separator": "{&}",
                    "separator": separator,
                    "max_tokens": 500,
                    "chunk_overlap": 1
                }
            }}

        retrieval_model = {
            "search_method": "semantic_search",
            "reranking_enable": False,
            "reranking_model": {
                "reranking_provider_name": reranking_provider_name,
                "reranking_model_name": reranking_model_name
            },
            "top_k": 3,
            "score_threshold_enabled": False,
            "score_threshold": 0.5
        }

        dataset_args = {
            "data_source": data_source,
            "indexing_technique": indexing_technique,
            "process_rule": process_rule,
            "doc_form": doc_form,
            "doc_language": doc_language,
            "retrieval_model": retrieval_model,
            "embedding_model": embedding_model,
            "embedding_model_provider": embedding_model_provider,
            "directory_id": directory_id
        }
        knowledge_config = KnowledgeConfig(**dataset_args)
        if knowledge_config.indexing_technique == "high_quality":
            if knowledge_config.embedding_model is None or knowledge_config.embedding_model_provider is None:
                raise ValueError("embedding model and embedding model provider are required for high quality indexing.")
            try:
                model_manager = ModelManager()
                model_manager.get_model_instance(
                    tenant_id=current_user.current_tenant_id,
                    provider=args["embedding_model_provider"],
                    model_type=ModelType.TEXT_EMBEDDING,
                    model=args["embedding_model"],
                )
            except InvokeAuthorizationError:
                raise ProviderNotInitializeError(
                    "No Embedding Model available. Please configure a valid provider in the Settings -> Model Provider."
                )
            except ProviderTokenNotInitError as ex:
                raise ProviderNotInitializeError(ex.description)

        # validate args
        DocumentService.document_create_args_validate(knowledge_config)

        if indexing_technique == "high_quality":
            try:
                model_manager = ModelManager()
                model_manager.get_model_instance(
                    tenant_id=tenant_id,
                    provider=embedding_model_provider,
                    model_type=ModelType.TEXT_EMBEDDING,
                    model=embedding_model,
                )
            except InvokeAuthorizationError:
                raise ProviderNotInitializeError(
                    "No Embedding Model available. Please configure a valid provider "
                    "in the Settings -> Model Provider."
                )
            except ProviderTokenNotInitError as ex:
                raise ProviderNotInitializeError(ex.description)

        # validate args
        # DocumentService.document_create_args_validate(args)

        try:
            dataset, documents, batch = DocumentService.save_document_without_dataset_id(
                tenant_id=tenant_id, knowledge_config=knowledge_config, account=current_user
            )
        except ProviderTokenNotInitError as ex:
            raise ProviderNotInitializeError(ex.description)
        except QuotaExceededError:
            raise ProviderQuotaExceededError()
        except ModelCurrentlyNotSupportError:
            raise ProviderModelCurrentlyNotSupportError()

        response = {"dataset": dataset, "documents": documents, "batch": batch}

        return response


class DatasetAddFileApi(Resource):

    # @marshal_with(file_fields)
    @marshal_with(dataset_and_document_fields)
    def post(self):
        file = request.files["file"]
        source = request.form.get("source")
        parser = reqparse.RequestParser()
        parser.add_argument("authorization", type=str, location="headers", required=True, help="Authorization header is required for authentication.")

        parser.add_argument('separator', type=str, location='form', required=True)
        parser.add_argument('embedding_model', type=str, location='form', required=True)
        parser.add_argument('embedding_model_provider', type=str, location='form', required=True)
        parser.add_argument('reranking_model_name', type=str, location='form', required=True)
        parser.add_argument('reranking_provider_name', type=str, location='form', required=True)
        parser.add_argument('dataset_id', type=str, location='form', required=True)
        parser.add_argument('tenant_id', type=str, location='form', required=True)
        parser.add_argument('account_id', type=str, location='form', required=True)
        args = parser.parse_args()

        if not validate_token(args['authorization'], CLIENT_SECRET, CLIENTS_TOKENS):
            return Response("Unauthorized", status=401)

        separator = args["separator"]
        embedding_model = args["embedding_model"]
        embedding_model_provider = args["embedding_model_provider"]
        reranking_model_name = args["reranking_model_name"]
        reranking_provider_name = args["reranking_provider_name"]
        tenant_id = args["tenant_id"]
        account_id = args["account_id"]

        indexing_technique = "high_quality"
        doc_form = "text_model"
        doc_language = "Chinese"

        dataset = DatasetService.get_dataset(args["dataset_id"])
        user = db.session.query(Account) \
            .filter(Account.id == account_id) \
            .first()
        tenant = TenantService.get_current_tenant_by_id(tenant_id)
        user.current_tenant = tenant

        if "file" not in request.files:
            raise NoFileUploadedError()

        if len(request.files) > 1:
            raise TooManyFilesError()

        if not file.filename:
            raise FilenameNotExistsError

        if source not in ("datasets", None):
            source = None

        try:
            upload_file = FileService.upload_file(
                filename=file.filename,
                content=file.read(),
                mimetype=file.mimetype,
                user=user,
                source=source,
            )
        except services.errors.file.FileTooLargeError as file_too_large_error:
            raise FileTooLargeError(file_too_large_error.description)
        except services.errors.file.UnsupportedFileTypeError:
            raise UnsupportedFileTypeError()

        data_source = {
            "type": "upload_file",
            "info_list": {
                "data_source_type": "upload_file",
                "file_info_list": {
                    "file_ids": [
                        upload_file.id
                    ]
                }
            }
        }

        process_rule = {
            "rules": {
                "pre_processing_rules": [
                    {
                        "id": "remove_extra_spaces",
                        "enabled": True
                    },
                    {
                        "id": "remove_urls_emails",
                        "enabled": False
                    }
                ],
                "segmentation": {
                    # "separator": "{&}",
                    "separator": separator,
                    "max_tokens": 500,
                    "chunk_overlap": 1
                }
            },
            "mode": "custom"
        }

        retrieval_model = {
            "search_method": "semantic_search",
            "reranking_enable": False,
            "reranking_model": {
                "reranking_provider_name": reranking_provider_name,
                "reranking_model_name": reranking_model_name
            },
            "top_k": 3,
            "score_threshold_enabled": False,
            "score_threshold": 0.5
        }

        dataset_args = {
            "data_source": data_source,
            "indexing_technique": indexing_technique,
            "process_rule": process_rule,
            "doc_form": doc_form,
            "doc_language": doc_language,
            "retrieval_model": retrieval_model,
            "embedding_model": embedding_model,
            "embedding_model_provider": embedding_model_provider,
        }

        if indexing_technique == "high_quality":
            try:
                model_manager = ModelManager()
                model_manager.get_model_instance(
                    tenant_id=tenant_id,
                    provider=embedding_model_provider,
                    model_type=ModelType.TEXT_EMBEDDING,
                    model=embedding_model,
                )
            except InvokeAuthorizationError:
                raise ProviderNotInitializeError(
                    "No Embedding Model available. Please configure a valid provider "
                    "in the Settings -> Model Provider."
                )
            except ProviderTokenNotInitError as ex:
                raise ProviderNotInitializeError(ex.description)

        # validate args
        # DocumentService.document_create_args_validate(args)

        try:
            documents, batch = DocumentService.save_document_with_dataset_id_for_outer(dataset, dataset_args, account_id, tenant_id)
        except ProviderTokenNotInitError as ex:
            raise ProviderNotInitializeError(ex.description)
        except QuotaExceededError:
            raise ProviderQuotaExceededError()
        except ModelCurrentlyNotSupportError:
            raise ProviderModelCurrentlyNotSupportError()

        response = {"documents": documents, "batch": batch}

        return response


def validate_token(authorization, client_secret, client_dict):
    token_type, token = authorization.split(None, 1)

    if token_type.lower() == 'bearer':
        try:
            decoded_token = jwt.decode(token, client_secret, algorithms=['HS256'])
            if 'client_id' in decoded_token:
                client_id = decoded_token['client_id']
                if client_id in client_dict:
                    logger.info(f"token={token} success")
                    return True
                else:
                    logger.warning(f"client_id={client_id} failed")
            else:
                logger.warning("client_id is not exist.")
        except jwt.InvalidTokenError:
            logger.warning("jwt.decode failed.")
    else:
        logger.warning("token type is not Bearer.")

    return False
