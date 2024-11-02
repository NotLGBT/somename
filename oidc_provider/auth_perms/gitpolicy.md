# GITPOLICY
1. Репозиторий состоит из 4х основных веток:
- authsubmodule-stable-dev
- authsubmodule-stable-master
- authsubmodule-experimental-dev
- authsubmodule-experimental-master
2. Ветки authsubmodule-stable-master и authsubmodule-experimental-master защищены от push и force push. Напрямую вливать в них можно только ветки с хотфиксами.
3. Для всего остального использовать merge request из authsubmodule-stable-dev/authsubmodule-experimental-dev
4. Выполнять merge request в authsubmodule-stable-master/authsubmodule-experimental-master ветки только с использованием squash
5. Для разработки создавать отдельные ветки из authsubmodule-stable-dev/authsubmodule-experimental-dev
6. Для релизов в authsubmodule-stable-master/authsubmodule-experimental-master ветках создавать в них аннотационный тег с указанием  версии authsubmodule, его типа и ветки. Пример: authsubmodule5.13-stable-master. В authsubmodule-stable-dev/authsubmodule-experimental-dev ветках, пример: authsubmodule5.13-experimental-dev
7. Релизные теги формата authsubmodule*-master защищены. Создавать теги могут только пользователи группы maintainers.
8. Создание тегов формата authsubmodule*-dev разрешено выполнять пользователям developers+maintainers групп, удалять такие теги запрещено
9. Для внесения изменений в существующий тег необходимо из него создать новую ветку, эту ветку merge request`ом слить с нужной основной веткой и создать новый тег с новым названием, указывая версию authsubmodule, его тип, ветку и номер задачи. Пример: authsubmodule5.13-stable-master-v4t6
10. После выполнения merge request все ветки кроме четырех основных необходимо удалять из репозитория
11. Обновлять информацию в readme.md о том с какими версиями остальных сервисов был протестирован authsubmodule backend
12. Каждому участнику, кроме мейнтенера, выставлять expiration date
