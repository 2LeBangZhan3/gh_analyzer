#!/usr/bin/env python3
"""一个简单的命令行待办事项（Todo List）程序。

数据保存在当前目录下的 ``tasks.json`` 文件中，程序退出后任务不会丢失。
"""

import argparse
import json
import os
import sys

DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tasks.json")


def load_tasks():
    """从文件中加载任务列表。文件不存在或内容损坏时返回空列表。"""
    if not os.path.exists(DATA_FILE):
        return []
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError):
        return []


def save_tasks(tasks):
    """将任务列表写入文件。"""
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(tasks, f, ensure_ascii=False, indent=2)


def add_task(tasks, text):
    """添加一条新任务，返回新任务的编号（从 1 开始）。"""
    task = {"id": len(tasks) + 1, "text": text, "done": False}
    tasks.append(task)
    return task["id"]


def delete_task(tasks, task_id):
    """按编号删除任务。删除成功后重新整理编号。返回是否删除成功。"""
    for task in tasks:
        if task["id"] == task_id:
            tasks.remove(task)
            _renumber(tasks)
            return True
    return False


def _renumber(tasks):
    """删除任务后重新给所有任务连续编号。"""
    for index, task in enumerate(tasks, start=1):
        task["id"] = index


def list_tasks(tasks):
    """打印所有任务。"""
    if not tasks:
        print("暂无任务。")
        return
    for task in tasks:
        mark = "[x]" if task["done"] else "[ ]"
        print(f"{task['id']}. {mark} {task['text']}")


def main():
    parser = argparse.ArgumentParser(
        description="命令行待办事项（Todo List）程序"
    )
    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # add 子命令
    parser_add = subparsers.add_parser("add", help="添加任务")
    parser_add.add_argument("text", help="任务内容")

    # delete 子命令
    parser_delete = subparsers.add_parser("delete", help="删除任务")
    parser_delete.add_argument("id", type=int, help="要删除的任务编号")

    # list 子命令
    subparsers.add_parser("list", help="查看所有任务")

    args = parser.parse_args()

    tasks = load_tasks()

    if args.command == "add":
        task_id = add_task(tasks, args.text)
        save_tasks(tasks)
        print(f"已添加任务 #{task_id}: {args.text}")
    elif args.command == "delete":
        if delete_task(tasks, args.id):
            save_tasks(tasks)
            print(f"已删除任务 #{args.id}")
        else:
            print(f"未找到编号为 {args.id} 的任务。", file=sys.stderr)
            sys.exit(1)
    elif args.command == "list":
        list_tasks(tasks)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
