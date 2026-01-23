import sqlite3
import logging
import os
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATABASE_PATH = "database.db"
BACKUP_PATH = f"database_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
REPAIRED_PATH = "database_repaired.db"

def backup_database():
    """Создание резервной копии базы данных"""
    try:
        if os.path.exists(DATABASE_PATH):
            import shutil
            shutil.copy2(DATABASE_PATH, BACKUP_PATH)
            logger.info(f"✅ Резервная копия создана: {BACKUP_PATH}")
            return True
        else:
            logger.warning("⚠️ Исходная база данных не найдена")
            return False
    except Exception as e:
        logger.error(f"❌ Ошибка создания резервной копии: {e}")
        return False

def check_database_integrity():
    """Проверка целостности базы данных"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # Пытаемся выполнить простой запрос
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        if tables:
            logger.info(f"✅ База данных содержит таблицы: {len(tables)}")
            
            # Проверяем основные таблицы
            required_tables = ['users', 'user_fruits']
            existing_tables = [table[0] for table in tables]
            
            for table in required_tables:
                if table in existing_tables:
                    logger.info(f"✅ Таблица '{table}' найдена")
                else:
                    logger.warning(f"⚠️ Таблица '{table}' отсутствует")
        
        conn.close()
        return True
        
    except sqlite3.DatabaseError as e:
        logger.error(f"❌ База данных повреждена: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Неизвестная ошибка: {e}")
        return False

def repair_database():
    """Восстановление базы данных"""
    
    print("\n" + "=" * 50)
    print("🔧 ВОССТАНОВЛЕНИЕ БАЗЫ ДАННЫХ")
    print("=" * 50)
    
    # 1. Создаем резервную копию
    logger.info("📁 Создаю резервную копию...")
    backup_database()
    
    # 2. Пытаемся восстановить данные
    try:
        logger.info("🔄 Пытаюсь восстановить данные...")
        
        # Пытаемся подключиться к поврежденной базе
        damaged_conn = None
        try:
            damaged_conn = sqlite3.connect(DATABASE_PATH)
            damaged_cursor = damaged_conn.cursor()
            
            # Пытаемся получить список таблиц
            damaged_cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = damaged_cursor.fetchall()
            
            if not tables:
                logger.warning("⚠️ В поврежденной базе нет таблиц")
                create_new_database()
                return
            
            logger.info(f"🔍 Найдено таблиц в поврежденной базе: {len(tables)}")
            
            # Создаем новую базу данных
            if os.path.exists(REPAIRED_PATH):
                os.remove(REPAIRED_PATH)
            
            new_conn = sqlite3.connect(REPAIRED_PATH)
            new_cursor = new_conn.cursor()
            
            # Создаем таблицы по шаблону
            create_database_structure(new_cursor)
            
            # Пытаемся восстановить данные из каждой таблицы
            recovered_data = {}
            
            for table_name_tuple in tables:
                table_name = table_name_tuple[0]
                
                try:
                    # Пытаемся получить данные из таблицы
                    damaged_cursor.execute(f"SELECT * FROM {table_name}")
                    rows = damaged_cursor.fetchall()
                    
                    if rows:
                        # Получаем названия столбцов
                        damaged_cursor.execute(f"PRAGMA table_info({table_name})")
                        columns_info = damaged_cursor.fetchall()
                        
                        if columns_info:
                            recovered_data[table_name] = {
                                'columns': columns_info,
                                'rows': rows
                            }
                            logger.info(f"✅ Восстановлено {len(rows)} строк из таблицы '{table_name}'")
                        else:
                            logger.warning(f"⚠️ Не удалось получить структуру таблицы '{table_name}'")
                    
                except Exception as e:
                    logger.warning(f"⚠️ Не удалось восстановить таблицу '{table_name}': {e}")
            
            damaged_conn.close()
            
            # Восстанавливаем данные в новой базе
            if recovered_data:
                restore_data_to_new_database(new_cursor, recovered_data)
                new_conn.commit()
                logger.info("✅ Данные успешно восстановлены в новой базе")
            else:
                logger.warning("⚠️ Не удалось восстановить данные, создаю пустую базу")
            
            new_conn.close()
            
            # Заменяем поврежденную базу на восстановленную
            if os.path.exists(DATABASE_PATH):
                os.remove(DATABASE_PATH)
            os.rename(REPAIRED_PATH, DATABASE_PATH)
            
            logger.info("✅ Восстановление завершено!")
            
        except Exception as e:
            logger.error(f"❌ Ошибка при восстановлении: {e}")
            create_new_database()
            
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
        create_new_database()

def create_database_structure(cursor):
    """Создание структуры базы данных"""
    
    # Таблица пользователей
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            language TEXT DEFAULT 'RUS',
            is_subscribed INTEGER DEFAULT 0,
            free_totems INTEGER DEFAULT 1,
            paid_totems INTEGER DEFAULT 1,
            last_check TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Таблица выбранных фруктов
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_fruits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            fruit_name TEXT,
            FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE,
            UNIQUE(user_id, fruit_name)
        )
    ''')
    
    # Таблица исключений подписок
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS subscription_exceptions (
            user_id INTEGER PRIMARY KEY,
            admin_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE
        )
    ''')
    
    logger.info("✅ Структура базы данных создана")

def restore_data_to_new_database(cursor, recovered_data):
    """Восстановление данных в новой базе"""
    
    for table_name, data in recovered_data.items():
        try:
            if table_name == 'users':
                # Восстанавливаем пользователей
                for row in data['rows']:
                    try:
                        cursor.execute('''
                            INSERT OR REPLACE INTO users 
                            (user_id, username, language, is_subscribed, free_totems, paid_totems, last_check, created_at)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        ''', row[:8] if len(row) >= 8 else row + (None,) * (8 - len(row)))
                    except:
                        pass
                        
            elif table_name == 'user_fruits':
                # Восстанавливаем фрукты
                for row in data['rows']:
                    try:
                        if len(row) >= 3:
                            cursor.execute('''
                                INSERT OR REPLACE INTO user_fruits (user_id, fruit_name)
                                VALUES (?, ?)
                            ''', (row[1], row[2]))
                    except:
                        pass
                        
            elif table_name == 'subscription_exceptions':
                # Восстанавливаем исключения
                for row in data['rows']:
                    try:
                        if len(row) >= 3:
                            cursor.execute('''
                                INSERT OR REPLACE INTO subscription_exceptions 
                                (user_id, admin_id, created_at)
                                VALUES (?, ?, ?)
                            ''', (row[0], row[1], row[2]))
                    except:
                        pass
                        
        except Exception as e:
            logger.warning(f"⚠️ Ошибка при восстановлении таблицы '{table_name}': {e}")

def create_new_database():
    """Создание новой базы данных"""
    logger.info("🆕 Создаю новую базу данных...")
    
    if os.path.exists(DATABASE_PATH):
        os.remove(DATABASE_PATH)
    
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    create_database_structure(cursor)
    
    conn.commit()
    conn.close()
    
    logger.info("✅ Новая база данных создана")

def run_integrity_check():
    """Запуск проверки целостности"""
    print("\n" + "=" * 50)
    print("🔍 ПРОВЕРКА ЦЕЛОСТНОСТИ БАЗЫ ДАННЫХ")
    print("=" * 50)
    
    if check_database_integrity():
        logger.info("✅ База данных в порядке")
        return True
    else:
        logger.warning("⚠️ База данных повреждена, требуется восстановление")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("🛠️  УТИЛИТА ВОССТАНОВЛЕНИЯ БАЗЫ ДАННЫХ")
    print("=" * 50)
    
    print("\n📋 ВАРИАНТЫ ДЕЙСТВИЙ:")
    print("1. Проверить целостность базы данных")
    print("2. Восстановить базу данных")
    print("3. Создать новую базу данных")
    print("4. Выход")
    
    choice = input("\nВыберите действие (1-4): ").strip()
    
    if choice == "1":
        run_integrity_check()
    elif choice == "2":
        repair_database()
    elif choice == "3":
        create_new_database()
        logger.info("✅ Новая база данных создана. Старая сохранена как backup.")
    elif choice == "4":
        print("👋 Выход...")
    else:
        print("❌ Неверный выбор")
    
    print("\n" + "=" * 50)
    print("ℹ️  ИНФОРМАЦИЯ:")
    print(f"• Текущая база: {DATABASE_PATH}")
    if os.path.exists(BACKUP_PATH):
        print(f"• Резервная копия: {BACKUP_PATH}")
    print("=" * 50)