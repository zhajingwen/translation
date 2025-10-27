"""
EPUB 文件诊断工具
用于检查 EPUB 文件的内容结构，帮助发现数据遗漏问题
"""
import sys
from ebooklib import epub
from bs4 import BeautifulSoup

def analyze_epub(epub_path):
    """分析 EPUB 文件的内容结构"""
    try:
        book = epub.read_epub(epub_path, options={"ignore_ncx": True})
    except Exception as e:
        print(f"无法读取 EPUB 文件: {e}")
        return
    
    print("=" * 80)
    print(f"EPUB 文件分析: {epub_path}")
    print("=" * 80)
    
    # 统计信息
    total_items = 0
    html_items = []
    image_items = []
    css_items = []
    font_items = []
    other_items = []
    
    # 支持的 HTML/XHTML MIME 类型
    html_types = [
        'application/xhtml+xml',
        'application/xhtml', 
        'text/html',
        'text/xhtml',
        'application/html+xml',
        'text/xml',
    ]
    
    for item in book.get_items():
        total_items += 1
        item_type = item.media_type
        item_name = item.get_name()
        
        if item_type in html_types:
            html_items.append((item_name, item_type))
        elif item_type.startswith('image/'):
            image_items.append((item_name, item_type))
        elif item_type == 'text/css':
            css_items.append((item_name, item_type))
        elif item_type.startswith('font/'):
            font_items.append((item_name, item_type))
        else:
            other_items.append((item_name, item_type))
    
    # 打印统计信息
    print(f"\n总项目数: {total_items}")
    print(f"HTML/XHTML 项: {len(html_items)}")
    print(f"图片项: {len(image_items)}")
    print(f"样式表项: {len(css_items)}")
    print(f"字体项: {len(font_items)}")
    print(f"其他项: {len(other_items)}")
    
    # 详细列出 HTML 项目
    print("\n" + "=" * 80)
    print("HTML/XHTML 内容列表:")
    print("=" * 80)
    for i, (name, mime_type) in enumerate(html_items, 1):
        print(f"\n[{i}] {name}")
        print(f"    类型: {mime_type}")
        
        # 尝试提取文本内容预览
        try:
            for item in book.get_items():
                if item.get_name() == name:
                    soup = BeautifulSoup(item.get_content(), 'html.parser')
                    
                    # 移除 script 和 style
                    for script in soup(["script", "style"]):
                        script.decompose()
                    
                    text = soup.get_text(separator=' ', strip=True)
                    text_length = len(text)
                    
                    print(f"    文本长度: {text_length} 字符")
                    
                    if text_length > 0:
                        preview = text[:100].replace('\n', ' ')
                        print(f"    内容预览: {preview}...")
                    else:
                        print(f"    警告: 此项内容为空")
                    
                    break
        except Exception as e:
            print(f"    错误: 无法解析内容 - {e}")
    
    # 列出其他类型
    if other_items:
        print("\n" + "=" * 80)
        print("其他类型项目:")
        print("=" * 80)
        for name, mime_type in other_items:
            print(f"  - {name} ({mime_type})")
    
    print("\n" + "=" * 80)
    print("分析完成")
    print("=" * 80)

if __name__ == '__main__':
    
    epub_path = ''
    analyze_epub(epub_path)