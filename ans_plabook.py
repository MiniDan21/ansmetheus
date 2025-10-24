import argparse

from ans.executor import Executor


def argparser():
    parser = argparse.ArgumentParser(
        prog="Ansmetheus",
        description="Ansmetheus утилита для запуска задач и мониторинг на узлах"
    )

    parser.add_argument("host_group", required=True, help="Название хоста или группы из inventory-файла")
    parser.add_argument("-i", "--inventory", required=True, nargs="+", help="Путь до inventory-файлов")
    parser.add_argument("-p", "--playbook", required=True, nargs="+", help="Путь до playbook-файлов")

    return parser.parse_args()
    
def main():
    args = argparser()

    executor = Executor(args.host_group, args.inventory)
    executor.execute_playbook(args.playbook)


if __name__ == "__main__":
    main()
