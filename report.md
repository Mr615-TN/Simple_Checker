# Simple Checker Report

## Error

```
Traceback (most recent call last):
  File "/home/tanish/GitHub/Simple_Checker/simple_checker.py", line 220, in <module>
    main()
    ~~~~^^
  File "/home/tanish/GitHub/Simple_Checker/simple_checker.py", line 199, in main
    results = run_smart(args.command, timeout=args.timeout)
  File "/home/tanish/GitHub/Simple_Checker/simple_checker.py", line 86, in run_smart
    proc = psutil.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
  File "/home/tanish/all_virtualenvs/SimpleChecker/lib/python3.13/site-packages/psutil/__init__.py", line 1416, in __init__
    self.__subproc = subprocess.Popen(*args, **kwargs)
                     ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
  File "/home/tanish/miniconda3/lib/python3.13/subprocess.py", line 1039, in __init__
    self._execute_child(args, executable, preexec_fn, close_fds,
    ~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                        pass_fds, cwd, env,
                        ^^^^^^^^^^^^^^^^^^^
    ...<5 lines>...
                        gid, gids, uid, umask,
                        ^^^^^^^^^^^^^^^^^^^^^^
                        start_new_session, process_group)
                        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/tanish/miniconda3/lib/python3.13/subprocess.py", line 1972, in _execute_child
    raise child_exception_type(errno_num, err_msg, err_filename)
PermissionError: [Errno 13] Permission denied: '/tmp/tmppjqdrirb.txt'

```