#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
批量修改markdown文件的categories字段
支持多种categories格式：
1. categories: Python
2. categories: [Java,JavaClass]
3. categories: 
   - [Database,ElasticSearch]
   - [OS,Shell]
"""

import os
import re
from pathlib import Path
from typing import List, Tuple, Optional


def parse_front_matter(content: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """
    解析markdown的YAML front matter
    返回: (front_matter, title, categories_text)
    """
    # 匹配YAML front matter (--- 到 ---)
    pattern = r'^---\s*\n(.*?)\n---\s*\n'
    match = re.match(pattern, content, re.DOTALL)
    
    if not match:
        return None, None, None
    
    front_matter = match.group(1)
    
    # 提取title
    title_match = re.search(r'^title:\s*(.+)$', front_matter, re.MULTILINE)
    title = title_match.group(1).strip() if title_match else "无标题"
    
    # 提取categories (支持多种格式)
    categories_text = extract_categories_text(front_matter)
    
    return front_matter, title, categories_text


def extract_categories_text(front_matter: str) -> Optional[str]:
    """
    提取categories的原始文本表示
    """
    # 方式1: categories: value (单行，值在同一行)
    # 注意：不能用\s*，因为会匹配换行符，改用[ \t]*只匹配空格和制表符
    match = re.search(r'^categories:[ \t]*(.+)$', front_matter, re.MULTILINE)
    if match:
        value = match.group(1).strip()
        if value:  # 不为空，说明是单行格式
            return value
        # 如果为空，说明是多行格式，继续检查方式2
    
    # 方式2: categories: (多行列表)
    # categories:
    # - xxx
    # - [a,b]
    match = re.search(r'^categories:\s*$', front_matter, re.MULTILINE)
    if match:
        lines = front_matter.split('\n')
        cat_index = -1
        for i, line in enumerate(lines):
            if re.match(r'^categories:\s*$', line):
                cat_index = i
                break
        
        if cat_index >= 0:
            # 收集后续的列表项
            cat_lines = []
            for i in range(cat_index + 1, len(lines)):
                line = lines[i]
                # 如果是列表项
                if re.match(r'^\s*-\s+', line):
                    cat_lines.append(line)
                # 如果遇到下一个字段，停止
                elif re.match(r'^[a-zA-Z_]+:', line):
                    break
                # 空行继续
                elif not line.strip():
                    continue
                else:
                    break
            
            if cat_lines:
                return '\n'.join(cat_lines)
    
    return None


def format_categories_display(categories_text: Optional[str]) -> str:
    """
    格式化categories用于显示
    """
    if categories_text is None:
        return "(未设置)"
    
    # 如果包含换行，说明是多行格式
    if '\n' in categories_text:
        return f"\n{categories_text}"
    else:
        return categories_text


def scan_markdown_files(base_dir: str) -> List[Tuple[str, str, str, Optional[str]]]:
    """
    扫描所有markdown文件
    返回: [(文件路径, 标题, categories_text, 完整内容)]
    """
    results = []
    base_path = Path(base_dir)
    
    for md_file in base_path.rglob('*.md'):
        try:
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            front_matter, title, categories_text = parse_front_matter(content)
            
            if front_matter is not None:
                results.append((str(md_file), title, categories_text, content))
        except Exception as e:
            print(f"⚠️  读取文件失败 {md_file}: {e}")
    
    return results


def update_categories(content: str, old_categories: Optional[str], new_categories: str) -> str:
    """
    更新markdown内容中的categories字段
    最小化改动，只替换categories部分
    """
    # 匹配YAML front matter
    pattern = r'^(---\s*\n)(.*?)(\n---\s*\n)'
    match = re.match(pattern, content, re.DOTALL)
    
    if not match:
        return content
    
    prefix = match.group(1)
    front_matter = match.group(2)
    suffix = match.group(3)
    rest_content = content[match.end():]
    
    # 替换categories
    new_front_matter = replace_categories_in_front_matter(front_matter, old_categories, new_categories)
    
    return prefix + new_front_matter + suffix + rest_content


def replace_categories_in_front_matter(front_matter: str, old_categories: Optional[str], new_categories: str) -> str:
    """
    在front matter中替换categories
    """
    # 情况1: 单行categories
    if old_categories and '\n' not in old_categories:
        # categories: xxx -> categories: new_value
        pattern = r'^categories:\s*.+$'
        replacement = f'categories: {new_categories}'
        new_fm = re.sub(pattern, replacement, front_matter, count=1, flags=re.MULTILINE)
        if new_fm != front_matter:
            return new_fm
    
    # 情况2: 多行categories
    if old_categories and '\n' in old_categories:
        lines = front_matter.split('\n')
        new_lines = []
        i = 0
        while i < len(lines):
            line = lines[i]
            # 找到categories:行
            if re.match(r'^categories:\s*$', line):
                # 保留categories:行
                new_lines.append(line)
                # 跳过所有旧的列表项
                i += 1
                while i < len(lines):
                    if re.match(r'^\s*-\s+', lines[i]):
                        i += 1
                    elif not lines[i].strip():
                        i += 1
                    else:
                        break
                
                # 添加新的categories值
                # 如果新值本身包含换行（多行格式），直接添加
                if '\n' in new_categories:
                    new_lines.append(new_categories)
                else:
                    # 如果新值是单行，需要添加 "- " 前缀保持多行格式
                    new_lines.append(f'- {new_categories}')
                continue
            else:
                new_lines.append(line)
            i += 1
        return '\n'.join(new_lines)
    
    # 情况3: categories为空或未设置
    pattern = r'^categories:\s*$'
    if re.search(pattern, front_matter, re.MULTILINE):
        replacement = f'categories: {new_categories}'
        return re.sub(pattern, replacement, front_matter, count=1, flags=re.MULTILINE)
    
    return front_matter


def match_categories(file_categories: Optional[str], search_categories: str) -> bool:
    """
    判断文件的categories是否匹配搜索条件
    精确匹配（支持多行列表格式）
    """
    if file_categories is None:
        return search_categories.lower() in ['none', 'null', '', '(未设置)']
    
    # 标准化处理：去除空格、转小写
    file_cat_normalized = file_categories.replace(' ', '').lower()
    search_normalized = search_categories.replace(' ', '').lower()
    
    # 情况1: 精确匹配整个categories
    if file_cat_normalized == search_normalized:
        return True
    
    # 情况2: 多行列表格式，匹配其中的任意一项（完整匹配）
    # 例如: categories:
    #       - [Ceph]
    #       - [Container,Kubernets]
    # 搜索 "Ceph" 能匹配 "- [Ceph]"，但不能匹配 "- [Database,Ceph]"
    if '\n' in file_categories:
        # 提取每一行的列表项
        lines = file_categories.split('\n')
        for line in lines:
            # 提取 "- [xxx]" 或 "- xxx" 格式，去掉前面的 "-" 和空格
            line_stripped = line.strip()
            if line_stripped.startswith('-'):
                line_stripped = line_stripped[1:].strip()
            line_normalized = line_stripped.replace(' ', '').lower()
            
            # 跳过空行
            if not line_normalized:
                continue
            
            # 精确匹配这一行
            if line_normalized == search_normalized:
                return True
            
            # 如果搜索的是单个值（不带方括号），匹配 [单个值] 的形式
            # 例如搜索 "Ceph" 能匹配 "[Ceph]"，但不能匹配 "[Database,Ceph]"
            if not search_normalized.startswith('['):
                if line_normalized == f'[{search_normalized}]':
                    return True
    
    return False


def filter_files_by_categories(files: List[Tuple], search_categories: str) -> List[Tuple]:
    """
    根据categories筛选文件
    """
    matched_files = []
    for file_info in files:
        filepath, title, categories, content = file_info
        if match_categories(categories, search_categories):
            matched_files.append(file_info)
    
    return matched_files


def main():
    print("=" * 70)
    print("Markdown Categories 批量修改工具")
    print("=" * 70)
    
    # 设置博客目录
    script_dir = Path(__file__).parent
    posts_dir = script_dir.parent / '_posts'
    
    if not posts_dir.exists():
        print(f"❌ 目录不存在: {posts_dir}")
        return
    
    print(f"\n📁 扫描目录: {posts_dir}")
    
    # 扫描所有markdown文件
    all_files = scan_markdown_files(str(posts_dir))
    
    if not all_files:
        print("❌ 未找到任何markdown文件")
        return
    
    print(f"\n✅ 找到 {len(all_files)} 个markdown文件")
    
    # 步骤1: 输入要查找的categories
    print("\n" + "=" * 70)
    print("步骤 1: 查找符合条件的文件")
    print("=" * 70)
    print("\n提示: 输入要查找的categories值（精确匹配）")
    print("示例: Ceph 或 Python 或 [Java,JavaClass]")
    print("\n匹配规则:")
    print("  - 搜索 'Ceph' 可匹配: categories: Ceph 或 [Ceph] 或多行中的 - [Ceph]")
    print("  - 搜索 'Ceph' 不会匹配: [Database,Ceph] (列表中的部分元素)")
    print("  - 搜索 '[Java,JavaClass]' 精确匹配完整列表")
    
    search_categories = input("\n请输入要查找的categories: ").strip()
    
    if not search_categories:
        print("❌ 查找条件不能为空")
        return
    
    # 筛选文件
    matched_files = filter_files_by_categories(all_files, search_categories)
    
    if not matched_files:
        print(f"\n❌ 未找到匹配 '{search_categories}' 的文件")
        return
    
    # 步骤2: 显示匹配的文件
    print(f"\n✅ 找到 {len(matched_files)} 个匹配的文件:")
    print("=" * 70)
    
    for i, (filepath, title, categories, _) in enumerate(matched_files, 1):
        rel_path = Path(filepath).relative_to(posts_dir.parent)
        cat_display = format_categories_display(categories)
        print(f"\n{i}. 【{title}】")
        print(f"   路径: {rel_path}")
        print(f"   Categories: {cat_display}")
    
    print("\n" + "=" * 70)
    
    # 步骤3: 输入新的categories
    print("\n步骤 2: 输入新的categories值")
    print("=" * 70)
    print("\n提示: 输入新的categories值来替换上述文件")
    print("示例: Python 或 [Java,JavaClass] 或 [Database,ElasticSearch]")
    
    new_categories = input("\n请输入新的categories值: ").strip()
    
    if not new_categories:
        print("❌ categories不能为空")
        return
    
    # 步骤4: 二次确认
    print("\n" + "=" * 70)
    print("步骤 3: 确认修改")
    print("=" * 70)
    print(f"\n即将修改 {len(matched_files)} 个文件:")
    print(f"  原始值: {search_categories}")
    print(f"  新值:   {new_categories}")
    
    confirm = input(f"\n⚠️  确认执行修改? (yes/no): ").strip().lower()
    
    if confirm not in ['yes', 'y']:
        print("❌ 已取消操作")
        return
    
    # 步骤5: 执行修改
    print("\n" + "=" * 70)
    print("执行修改中...")
    print("=" * 70)
    
    success_count = 0
    for filepath, title, old_categories, content in matched_files:
        try:
            new_content = update_categories(content, old_categories, new_categories)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_content)
            success_count += 1
            print(f"✅ 已修改: {title}")
        except Exception as e:
            print(f"❌ 修改失败 {title}: {e}")
    
    print(f"\n🎉 完成! 成功修改 {success_count}/{len(matched_files)} 个文件")


if __name__ == '__main__':
    main()
