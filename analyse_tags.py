import os
import re
from collections import Counter

def analyze_text_files():
    """
    Рекурсивно извлекает данные из текстовых файлов в текущей папке и анализирует их.
    Считает данные в круглых скобках одним тегом.
    Обрабатывает запятые и переносы строк как разделители тегов.
    Если нет 'Negative prompt', обрабатывает только первую строку.
    Удаляет переносы строк и начальные пробелы в результатах.
    Сохраняет результаты в файл _result.txt с общим количеством повторений,
    отсортированным по убыванию частоты, а при равном количестве - по алфавиту.
    """
    all_tags = []

    for root, _, files in os.walk('.'):
        for file in files:
            if file.endswith('.txt'):
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                        negative_prompt_index = content.find("Negative prompt")

                        if negative_prompt_index != -1:
                            data_to_analyze = content[:negative_prompt_index].strip()
                        else:
                            # Обрабатываем только первую строку, если нет "Negative prompt"
                            data_to_analyze = content.split('\n', 1)[0].strip()

                        # Правим 33 строку: заменяем ", " и переносы строк на ","
                        data_to_analyze = data_to_analyze.replace(',\n', ',').replace('\n', ',')

                        # Разделяем строку на теги, учитывая запятые и скобки
                        tags_found = re.findall(r'[^,()]+|\([^()]*\)', data_to_analyze)

                        for tag_str in tags_found:
                            tag = tag_str.strip().lower()
                            if tag:
                                all_tags.append(tag)

                except Exception as e:
                    print(f"Ошибка при обработке файла {filepath}: {e}")

    tag_counts = Counter(all_tags)

    # Сортируем теги по количеству повторений в убывающем порядке,
    # а при равном количестве - по алфавиту
    sorted_tags = sorted(tag_counts.items(), key=lambda item: (-item[1], item[0]))

    with open('_result.txt', 'w', encoding='utf-8') as outfile:
        for tag, count in sorted_tags:
            outfile.write(f"{tag.strip()} - {count}\n")

    print("Анализ завершен. Результаты сохранены в файле _result.txt.")

if __name__ == "__main__":
    analyze_text_files()