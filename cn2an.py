import os
import re
import logging
from pathlib import Path
from typing import Dict, Optional, NoReturn, List, Tuple

# 从config导入版本信息
from config import __version__

# 中文数字到阿拉伯数字的映射常量
CHINESE_NUM_MAP: Dict[str, int] = {
    '零': 0, '一': 1, '二': 2, '三': 3, '四': 4, '五': 5, '六': 6, '七': 7, '八': 8, '九': 9,
    '十': 10, '百': 100, '千': 1000, '万': 10000, '亿': 100000000
}

# 中文数字匹配模式（预编译提升性能）
CHINESE_NUM_PATTERN = re.compile(r'第([一二三四五六七八九十百千万亿零]+)')

def validate_chinese_number(chinese_num: str) -> None:
    """
    验证中文数字字符串是否只包含有效字符
    :param chinese_num: 中文数字字符串
    :raises ValueError: 如果包含无效字符
    """
    invalid_chars = [c for c in chinese_num if c not in CHINESE_NUM_MAP]
    if invalid_chars:
        raise ValueError(f"包含无效的中文数字字符: {', '.join(invalid_chars)}")


def chinese_to_arabic(chinese_num: str) -> int:
    if not chinese_num:
        raise ValueError("中文数字字符串不能为空")
    """
    将中文数字转换为阿拉伯数字
    :param chinese_num: 中文数字字符串（如'一', '十', '一百二十三', '十亿'）
    :return: 对应的阿拉伯数字
    :raises ValueError: 如果包含无效字符
    """
    # 验证输入
    validate_chinese_number(chinese_num)

    # 处理特殊情况：单独的"十"表示10
    if chinese_num == '十':
        return 10

    # 中文数字转换核心算法
    # 定义单位值映射
    unit_map = {
        '十': 10,
        '百': 100,
        '千': 1000,
        '万': 10000,
        '亿': 100000000
    }
    # 基础数字值映射
    num_map = {
        '一': 1,
        '二': 2,
        '三': 3,
        '四': 4,
        '五': 5,
        '六': 6,
        '七': 7,
        '八': 8,
        '九': 9
    }

    # 初始化变量
    result = 0
    current_section = 0  # 当前小节（个级）
    temp_value = 0       # 当前临时值

    for char in chinese_num:
        if char in num_map:
            # 当前字符是数字
            temp_value = temp_value * 10 + num_map[char]
        elif char == '零':
            # 处理零
            current_section += temp_value
            temp_value = 0
        elif char in unit_map:
            # 当前字符是单位
            unit_val = unit_map[char]
            
            # 如果没有前置数字，默认为1（如"十"表示10）
            if temp_value == 0:
                temp_value = 1
            
            # 处理高级单位（万和亿）
            if unit_val >= 10000:
                # 先将临时值加到当前小节
                current_section += temp_value
                # 将当前小节乘以高级单位并加到结果
                result += current_section * unit_val
                # 重置当前小节
                current_section = 0
            else:
                # 处理低级单位（十、百、千）
                current_section += temp_value * unit_val
            
            # 重置临时值
            temp_value = 0

    # 添加最后剩余的值
    current_section += temp_value
    result += current_section

    return result


def process_files(target_path: Path) -> None:
    """
    处理目标目录中的文件，将中文数字文件名转换为阿拉伯数字
    :param target_path: 目标目录路径
    """
    if not target_path.exists():
        logging.error(f"错误: 目录 '{target_path}' 不存在，请检查路径是否正确")
        return

    if not target_path.is_dir():
        logging.error(f"错误: '{target_path}' 不是一个目录")
        return

    files = [entry for entry in target_path.iterdir() if entry.is_file()]
    total_files = len(files)
    processed_files = 0
    renamed_files = 0

    logging.info(f"开始处理: 共发现 {total_files} 个文件")

    for entry in files:
        processed_files += 1
        if process_single_file(entry):
            renamed_files += 1

    logging.info(f"处理完成: 共处理 {processed_files} 个文件，成功重命名 {renamed_files} 个文件")


def process_single_file(file_path: Path) -> bool:
    """
    处理单个文件，检查并转换文件名中的中文数字
    :param file_path: 文件路径
    :return: 如果文件被成功重命名则返回True，否则返回False
    """
    match = CHINESE_NUM_PATTERN.search(file_path.name)
    if not match:
        logging.debug(f"文件 '{file_path.name}' 不符合命名格式，已跳过")
        return False

    chinese_number = match.group(1)
    try:
        num = chinese_to_arabic(chinese_number)
        new_name = re.sub(rf'第{re.escape(chinese_number)}', str(num), file_path.name, count=1)

        if new_name == file_path.name:
            logging.warning(f"警告: 文件名 '{file_path.name}' 未发生变化，已跳过")
            return False

        new_path = file_path.parent / new_name

        if not file_path.exists():
            logging.error(f"错误: 文件 '{file_path}' 不存在，已跳过")
            return False

        if new_path.exists():
            logging.error(f"错误: 新文件名 '{new_name}' 已存在，文件 '{file_path.name}' 已跳过")
            return False

        file_path.rename(new_path)
        logging.info(f"成功重命名: {file_path.name} -> {new_name}")
        return True

    except ValueError as e:
        logging.error(f"格式错误: {e}，文件 '{file_path.name}' 已跳过")
        return False
    except Exception as e:
        logging.error(f"处理文件 '{file_path.name}' 时出错: {str(e)}")
        return False


def exit_with_error(message: str, exit_code: int = 1) -> NoReturn:
    """
    输出错误消息并退出程序
    :param message: 错误消息
    :param exit_code: 退出码
    """
    logging.error(message)
    exit(exit_code)


def configure_logging(verbose: bool = False) -> None:
    """
    配置日志系统
    :param verbose: 如果为True，则启用DEBUG级别日志
    """
    log_level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


def preview_conversions(folder_path, match_pattern=r'第{cn_num}', replace_pattern=r'{an_num}'):
    """
    预览文件转换效果，返回转换列表但不实际修改文件
    
    Args:
        folder_path: 目标文件夹路径
        match_pattern: 匹配模式，包含{cn_num}占位符表示中文数字位置
        replace_pattern: 替换模式，包含{an_num}占位符表示阿拉伯数字位置
        
    Returns:
        转换列表，每个元素是(原文件entry, 新文件名)的元组
    """
    conversion_list = []
    # 解析匹配模式，将{cn_num}替换为中文数字正则表达式
    cn_num_regex = r'([零一二三四五六七八九十百千万亿]+)'
    # 转义特殊字符，但保留{cn_num}的替换
    regex_pattern = re.escape(match_pattern).replace(r'\{cn_num\}', cn_num_regex)
    pattern = re.compile(regex_pattern)
    
    for entry in os.scandir(folder_path):
        if entry.is_file():
            match = pattern.search(entry.name)
            if match:
                chinese_number = match.group(1)
                try:
                    num = chinese_to_arabic(chinese_number)
                    # 应用替换模式
                    new_name = pattern.sub(replace_pattern.replace('{an_num}', str(num)), entry.name, count=1)
                    conversion_list.append((entry, new_name))
                except ValueError as e:
                    logging.warning(f"无法转换中文数字: {chinese_number}, 错误: {e}")
    
    return conversion_list


def perform_conversions(conversion_list):
    """
    执行文件转换，实际修改文件名
    
    Args:
        conversion_list: 由preview_conversions返回的转换列表
        
    Returns:
        成功转换的文件数量
    """
    success_count = 0
    for entry, new_name in conversion_list:
        try:
            new_path = os.path.join(os.path.dirname(entry.path), new_name)
            os.rename(entry.path, new_path)
            success_count += 1
            logging.info(f"已转换: {entry.name} -> {new_name}")
        except Exception as e:
            logging.error(f"转换失败: {entry.name}, 错误: {e}")
    
    return success_count


if __name__ == "__main__":
    # 保留命令行功能
    import argparse
    parser = argparse.ArgumentParser(description=f'{__version__}中文数字文件名转换工具 v{__version__}')
    parser.add_argument('--path', default='.', help='目标目录路径')
    parser.add_argument('-v', '--verbose', action='store_true', help='显示详细日志信息')
    parser.add_argument('--version', action='version', version=f'%(prog)s {__version__}')
    args = parser.parse_args()

    configure_logging(args.verbose)
    try:
        target_path = Path(args.path).resolve()
        process_files(target_path)
    except Exception as e:
        exit_with_error(f"程序执行出错: {str(e)}")