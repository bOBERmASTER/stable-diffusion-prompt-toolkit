import os
from PIL import Image
from PIL.ExifTags import TAGS

def extract_jpg_metadata(image_path):
    """Извлекает поле UserComment из метаданных JPG."""
    try:
        with Image.open(image_path) as img:
            exif = img._getexif()
            if exif:
                for tag, value in exif.items():
                    tag_name = TAGS.get(tag, tag)
                    if tag_name == "UserComment":
                        if isinstance(value, bytes):
                            return value[8:].decode('utf-16be', errors='ignore').strip()
                        return str(value).strip()
                    # Add this to handle IfdTag objects
                    elif isinstance(value, int) or isinstance(value, str) or isinstance(value, bytes) :
                        pass # It's a simple value, but not UserComment, so we skip
                    else:
                        print(f"Skipping tag {tag_name} with type {type(value)}") # Optional: Print info about skipped tags
        return None
    except Exception as e:
        print(f"Ошибка при извлечении метаданных из JPG {image_path}: {e}")
        return None

def extract_png_metadata(image_path):
    """Извлекает поле parameters из метаданных PNG."""
    try:
        with Image.open(image_path) as img:
            parameters = img.info.get("parameters")
            if parameters:
                return parameters.strip()
        return None
    except Exception as e:
        print(f"Ошибка при извлечении метаданных из PNG {image_path}: {e}")
        return None

def save_metadata_to_file(metadata, output_path):
    """Сохраняет метаданные в текстовый файл, если есть 'Seed'."""
    if metadata and "Seed" in metadata:
        try:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(metadata)
            print(f"Метаданные сохранены в {output_path}")
        except Exception as e:
            print(f"Ошибка при сохранении файла {output_path}: {e}")
    elif metadata:
        print(f"В метаданных отсутствует 'Seed'. Файл {output_path} не сохранен.")

def process_images_in_folder(folder_path):
    """Обрабатывает все изображения в указанной папке и подпапках."""
    # os.walk уже обеспечивает рекурсивный обход дерева каталогов
    for root, _, files in os.walk(folder_path):
        for file in files:
            if file.lower().endswith(('.jpg', '.jpeg', '.png')):
                image_path = os.path.join(root, file)
                base_name, _ = os.path.splitext(file)
                output_file = os.path.join(root, base_name + ".txt")

                if os.path.exists(output_file):
                    print(f"Текстовый файл {output_file} уже существует. Пропускаем.")
                    continue

                print(f"Обработка файла: {image_path}")
                metadata = None
                if file.lower().endswith(('.jpg', '.jpeg')):
                    metadata = extract_jpg_metadata(image_path)
                elif file.lower().endswith('.png'):
                    metadata = extract_png_metadata(image_path)

                if metadata:
                    save_metadata_to_file(metadata, output_file)
                else:
                    print(f"Не удалось извлечь метаданные из {image_path}")

if __name__ == "__main__":
    current_folder = os.getcwd()
    process_images_in_folder(current_folder)