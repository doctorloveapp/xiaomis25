import sys

if __name__ == '__main__':
    if len(sys.argv)>1:
        from s5studio.cli import run
        try:
            code=run(sys.argv[1:])
        except Exception:
            import traceback
            detail=traceback.format_exc()
            if sys.stderr is not None:
                sys.stderr.write(detail)
            else:
                from s5studio.paths import user_data_root
                directory=user_data_root();directory.mkdir(parents=True,exist_ok=True)
                (directory/'cli-error.log').write_text(detail,encoding='utf8')
            code=1
        raise SystemExit(code)
    from s5studio.web_ui import launch
    raise SystemExit(launch())
