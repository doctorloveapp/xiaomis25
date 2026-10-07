import sys

if __name__ == '__main__':
    if len(sys.argv)>1:
        from s5studio.cli import run
        raise SystemExit(run(sys.argv[1:]))
    from s5studio.web_ui import launch
    raise SystemExit(launch())
