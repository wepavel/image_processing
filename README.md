# Сервис обработки изображений

---

## Установка

---

###  docker-compose.yml

```yaml
services:
  image-processing:
    image: 'image-processing:latest'
    depends_on:
      - rabbitmq
      - image-processing-worker
    build:
      context: ./
    restart: always
    volumes:
      - ./config.yaml:/config.yaml
      - ./src:/app/src
    command: ["python", "app.py"]
    ports:
      - 8024:8001
    networks:
      - image-processing-net

  rabbitmq:
    image: rabbitmq:4.1.1-management
    restart: always
    volumes:
      - ./rabbitmq:/var/lib/rabbitmq
      - ./rabbitmq.conf:/etc/rabbitmq/rabbitmq.conf
      - ./definitions.json:/etc/rabbitmq/definitions.json
      - /etc/localtime:/etc/localtime:ro
    expose:
      - 5672
    ports:
      - 15672:15672
    networks:
      - image-processing-net

  image-processing-worker:
    image: 'image-processing-worker:latest'
    restart: always
    build:
      context: ./
    depends_on:
      - rabbitmq
    volumes:
      - ./config.yaml:/config.yaml
      - ./tmp:/tmp
      - ./src:/app/src
    command: ["python", "-u", "./scripts/tasks_worker.py"]
    networks:
      - image-processing-net

networks:
  image-processing-net:
    external: true
    name: image-processing-net
```

### Запуск
. `docker compose up -d`


### Пояснение к архитектуре

`image-processing` - публичный эндпоинт API, через который можно получать и создавать задачи.

`image-processing-worker` - воркер обработки.

### config.yaml

```yaml
tmp_dir: /tmp

pg:
  host: postgres
  port: 5432
  user: postgres
  password: postgres
  database: database
  schema: tasks

rabbit:
  host: rabbitmq
  port: 5672
  user: admin
  password: administrator
  queue_name: task_queue
  exchange: image_tasks_exchange
  routing_key: img_process

image_requests:
  host: files
  port: 8001
  schema: http
  path_prefix: /api
  chunk_size: 5242880
```

### Переменные окружения (опциональные)

- YAML_PATH=/config.yaml

## API

---

### Добавление задачи обработки
**Описание:** Создаёт задачу на обработку изображения.

`POST /api/tasks/`

**Запрос** `application/json`
- **JSON тело запроса (`CreationModel`):**
```json5
{
    // id изображения в хранилище
    "image_id": "image_id",
    // Название функции для заданного действия
    "function_type": "function_type",
    // Аргументы заданной функции
    "function_args": {
        "arg1": "arg_value1",
        "arg2": 1
    }
}
```

**Ответ** `application/json` `200 OK`

```json5
{
    // Время создания задачи
    "created_at": "2025-07-07T10:14:44.575222",
    // Длительность выполнения задачи
    "duration": null,
    // Заданные аргументы функции
    "function_args": {
        "target_srs": "EPSG:3857"
    },
    // Название функции для заданного действия
    "function_type": "change_projection",
    // id изображения в хранилище
    "image_id": "0197e45a-8fc5-e848-dc9f-56cc0ae0a087",
    // id измененного изображения в хранилище
    "new_image_id": null,
    // Текущий статус задачи в системе
    "status": "new",
    // id текущей задачи
    "task_id": 111,
    // Время последнего изменения задачи
    "updated_at": "2025-07-07T10:14:44.575156"
}
```

**Ошибки**:

- `400` - ошибки в параметрах запроса.
- `500` - прочие ошибки.


### Список задач обработки
**Описание:** Создаёт задачу на обработку изображения.


`GET /api/tasks/`

**Ответ** `application/json` `200 OK`

Аналогичен ответу добавления задачи, все доступные задачи.

**Ошибки**:

- `400` - ошибки в параметрах запроса.
- `500` - прочие ошибки.

### Информация о задаче обработки

`GET /api/tasks/<task_id>/`

**Запрос** `application/json`
- **Path-параметр**
  - `task_id` — идентификатор задачи.

**Ответ** `application/json` `200 OK`

Аналогичен ответу добавления задачи.

**Ошибки**:

- `400` - ошибки в параметрах запроса.
- `500` - прочие ошибки.