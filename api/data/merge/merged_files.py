# 导入必要的库

# 要合并的txt文件列表
txt_files = ['scu_stopwords.txt', 'hit_stopwords.txt', 'cn_stopwords.txt', 'baidu_stopwords.txt']

# 用于存储合并后的内容
merged_lines = set()

# 读取每个txt文件的内容，并去重后添加到集合中
for file in txt_files:
    with open(file) as f:
        lines = f.readlines()
        merged_lines.update(lines)

# 将合并后的内容写入新的txt文件
output_file = 'merged_output.txt'
with open(output_file, 'w') as f:
    f.writelines(merged_lines)

print(f'Merged and deduplicated content has been saved to {output_file}.')
