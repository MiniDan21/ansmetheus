import argparse

from ans.executor import Executor


def argparser():
    parser = argparse.ArgumentParser(
        prog="Ansmetheus",
        description="Ansmetheus утилита для запуска задач и мониторинг на узлах"
    )

    parser.add_argument("host_group", help="Название хоста или группы из inventory-файла")
    parser.add_argument("-i", "--inventory", required=True, nargs="+", help="Путь до inventory-файлов")

    parser.add_argument("-m", "--module", required=True, help="Название модуля для исполнения")
    parser.add_argument(
        "-a", "--args",
        nargs="*",
        metavar="KEY=VALUE",
        help="Аргументы модуля в формате key=value (например: name=curl state=present)"
    )
    parser.add_argument("-s", "--sudo", action="store_true", help="Выполнить задачи в роли sudo")

    return parser.parse_args()

def parse_module_args(arg_list):
    args_dict = {}
    if not arg_list:
        return args_dict

    for pair in arg_list:
        if "=" not in pair:
            raise ValueError(f"Неверный формат аргумента: {pair}. Используй key=value")
        key, value = pair.split("=", 1)
        args_dict[key] = value
    return args_dict

def main():
    args = argparser()
    module_args = parse_module_args(args.args)
    
    executor = Executor(args.host_group, args.inventory)
    executor.execute_module(args.module, args.sudo, **module_args)


if __name__ == "__main__":
    main()
