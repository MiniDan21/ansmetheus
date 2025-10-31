import argparse
from .storage import JobStorage

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--add", nargs="+", help="Add job schedule + command")
    args = parser.parse_args()

    if args.add:
        schedule, cmd = args.add[0], " ".join(args.add[1:])
        js = JobStorage()
        jobs = js.load()
        jobs.append({"schedule": schedule, "command": cmd})
        js.save(jobs)
        print("✅ Job added")
