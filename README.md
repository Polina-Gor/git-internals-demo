1. Запуск приложения
Запуск команд производится из корня репозитория.

Сборка образов и запуск контейнеров:
docker compose up --build -d

Проверка состояния контейнеров:
docker compose ps

Адрес приложения:
http://localhost:8080

Остановка приложения:
docker compose down

2. Архитектура
Ноутбук
  |
  v
Linux VM
  |
  v
Docker Compose
  |
  +--> frontend (порт 8080)
  |       |
  |       +--> запросы /api/
  |                 |
  |                 v
  +------------> backend (порт 5000)

Frontend доступен через опубликованный порт '8080'. Запросы к '/api/' перенаправляются на backend по адресу 'http://backend:5000/api/' внутри сети Docker Compose.

3. Проверка взаимодействия frontend и backend
1. Запустить приложение командой 'docker compose up --build -d'.
2. Открыть в браузере 'http://localhost:8080'.
3. Убедиться, что страница получает данные от backend.
4. При необходимости открыть инструменты разработчика браузера, вкладку Network, и проверить запрос к '/api/' и его ответ.
5. Проверить состояние контейнеров командой 'docker compose ps'.
При развёртывании на VM вместо 'localhost' следует использовать IP-адрес виртуальной машины, если порт '8080' доступен с ноутбука.
Результат проверки: frontend открывается по адресу 'http://localhost:8080', запрос к '/api/' возвращает данные от backend.

4. Проверка доступности KVM
Конфигурация компьютера
- ОС хоста: Windows 10 Pro, версия 22H2, сборка 19045.
- Архитектура процессора: x86-64.
- Процессор: AMD Ryzen 5 5500U.
- Используются WSL2 с Ubuntu, Docker Desktop и Oracle VirtualBox 7.2.2.

Проверки виртуализации
На Windows проверено состояние виртуализации через Диспетчер задач и команду:
systeminfo

В Диспетчере задач виртуализация указана как включённая. В выводе 'systeminfo' присутствует сообщение об обнаруженном гипервизоре.
Дополнительно проверена конфигурация загрузчика:
bcdedit /enum "{current}"

Параметр `hypervisorlaunchtype` установлен в `Auto`.
В WSL2 выполнены команды:
uname -a
systemd-detect-virt
grep -m1 -E 'vmx|svm' /proc/cpuinfo
ls -l /dev/kvm

Результаты: система определяется как WSL, флаги 'vmx'/'svm' в '/proc/cpuinfo' не найдены, устройство '/dev/kvm' отсутствует.

В VirtualBox проверена конфигурация виртуальной машины:
VBoxManage list hostinfo
VBoxManage showvminfo "team_3"

Для гостевой Ubuntu проверены:
uname -a
systemd-detect-virt
lscpu
grep -m1 -E 'vmx|svm' /proc/cpuinfo
ls -l /dev/kvm
sudo modprobe kvm_amd

Гостевая система определяется как VirtualBox. В её выводе отсутствуют флаги 'vmx'/'svm', устройство '/dev/kvm' отсутствует. Загрузка модуля 'kvm_amd' завершается ошибкой 'SVM not supported by CPU 3'.

Вывод по диагностике
Несмотря на включённую виртуализацию на Windows, в проверенных вложенных окружениях WSL2 и VirtualBox аппаратные возможности, необходимые для работы KVM, не доступны гостевой системе. Поэтому создать и запустить KVM-виртуальную машину в проверенной конфигурации не удалось.
Это подтверждает ограничение текущей конфигурации вложенной виртуализации, но не доказывает невозможность использования KVM непосредственно на физическом Linux-хосте.

5. Предполагаемая конфигурация Linux VM
Для выполнения задания на подходящем Linux-хосте предполагается создать виртуальную машину Ubuntu Server x86-64 с доступом по SSH и сетевым интерфейсом, доступным с ноутбука.
Пример создания диска виртуальной машины с помощью 'qemu-img':
qemu-img create -f qcow2 ubuntu-server.qcow2 20G

Пример запуска установки через 'virt-install' на хосте с работающим KVM и установленным 'libvirt':
sudo virt-install \
  --name docker-ansible-vm \
  --memory 2048 \
  --vcpus 2 \
  --disk path=ubuntu-server.qcow2,format=qcow2 \
  --cdrom /path/to/ubuntu-server.iso \
  --os-variant ubuntu24.04 \
  --network network=default \
  --graphics none \
  --console pty,target_type=serial

Перед запуском необходимо заменить '/path/to/ubuntu-server.iso' на путь к ISO-образу Ubuntu Server. Для доступа с ноутбука необходимо настроить сеть VM и определить её реальный IP-адрес.

6. Ansible: inventory

Файл 'ansible/inventory.ini':
[app_servers]
linux_vm ansible_host=192.168.56.10 ansible_user=ubuntu

[app_servers:vars]
ansible_ssh_private_key_file=~/.ssh/id_rsa

Адрес '192.168.56.10', имя пользователя 'ubuntu' и путь к ключу приведены как пример. Перед реальным развёртыванием их необходимо заменить параметрами доступной Linux VM.

7. Ansible: playbook
Файл 'ansible/playbook.yml':
---
- name: Deploy the application
  hosts: app_servers
  become: true

  vars:
    app_dir: /opt/git-internals-demo
    project_dir: "{{ playbook_dir }}/.."

  tasks:
    - name: Install Docker and Docker Compose
      ansible.builtin.apt:
        name:
          - docker.io
          - docker-compose-v2
        state: present
        update_cache: true

    - name: Ensure Docker is running
      ansible.builtin.service:
        name: docker
        state: started
        enabled: true

    - name: Create application directory
      ansible.builtin.file:
        path: "{{ app_dir }}"
        state: directory
        mode: "0755"

    - name: Copy Docker Compose configuration
      ansible.builtin.copy:
        src: "{{ project_dir }}/compose.yaml"
        dest: "{{ app_dir }}/compose.yaml"
        mode: "0644"

    - name: Copy application source code
      ansible.builtin.copy:
        src: "{{ project_dir }}/app/"
        dest: "{{ app_dir }}/app/"
        mode: preserve

    - name: Build and start application
      ansible.builtin.command:
        cmd: docker compose up --build -d
        chdir: "{{ app_dir }}"

Playbook устанавливает Docker и Docker Compose, запускает службу Docker, создаёт каталог приложения, копирует 'compose.yaml' и исходники, затем собирает и запускает сервисы.

8. Проверка Ansible
В Ubuntu WSL установлена Ansible Core 2.21.5.
Синтаксис playbook проверен командой:
ansible-playbook -i ansible/inventory.ini --syntax-check ansible/playbook.yml

Команда завершилась без синтаксических ошибок.

Состав inventory проверен командой:
ansible-inventory -i ansible/inventory.ini --graph

Ansible распознал группу 'app_servers' и хост 'linux_vm'.

Подключение проверялось командой:
ansible -i ansible/inventory.ini app_servers -m ansible.builtin.ping

Подключение завершилось ошибкой `Connection timed out` при обращении к `192.168.56.10:22`. Указанный адрес используется как пример и не подтверждён как адрес работающей VM. Поэтому успешный запуск playbook на целевом сервере и развёртывание приложения через Ansible пока не подтверждены.

9. Проверка развёртывания на подходящем Linux-хосте
После создания доступной VM и настройки SSH необходимо:

1. Указать действительные IP-адрес, пользователя и путь к SSH-ключу в 'ansible/inventory.ini'.
2. Проверить SSH-доступ и доступность хоста через Ansible.
3. Проверить синтаксис playbook.
4. Запустить развёртывание из корня репозитория:
   ansible-playbook -i ansible/inventory.ini ansible/playbook.yml
5. Подключиться к VM и проверить контейнеры:
   cd /opt/git-internals-demo
   docker compose ps
6. Открыть 'http://<IP-адрес-VM>:8080' с ноутбука и проверить получение данных от backend.
7. Повторно выполнить playbook и проверить, что сервисы продолжают работать.

Успешным результатом проверки будет доступность frontend с ноутбука, корректный ответ backend и работающие контейнеры после выполнения playbook.