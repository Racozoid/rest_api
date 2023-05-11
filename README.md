### REST API с использование aiohttp и Redis
Приложение и Redis работают локально. 

Запуск через docker-compose не реализован, поэтому необходимо:
1. Запустить redis-server
2. Запустить main.py
3. Отправить запрос на http://localhost:8080/
