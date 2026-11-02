# ntj_fconvert

**ntj_fconvert** is an **ntJobsApp** that converts files between formats through a single `CONVERT` command: it reads one or more input files (`FILE.IN` / `FILE.IN.N`) and produces an output file in the requested format.

It supports two families of conversions:

- **DFC** — generic structured conversions between `ini`, `xls/xlsx`, `xml`, `json`, `yaml`, `csv` and `txt`
- **PDF** — PDF → Markdown, Excel (tabular extraction) and Word

## What is an ntJobsApp?

An **ntJobsApp** is a job-oriented Python application built on the `acJobsApp` framework: it reads a job `.ini` file (a `[CONFIG]` section plus one or more `[JOB_*]` sections), executes every `COMMAND` in sequence and writes a `.end` result file. For the full framework definition see the `acJobsApp.py` / `aiSys.py` files shipped with this app (part of ntjobsOS).

## Quick start

```
ntj_fconvert.cmd myjob.ini          # Windows
./ntj_fconvert.sh myjob.ini         # Linux
```

## Documentation

For the full manual — conversion types, TYPE/ENGINE matrix, parameters and concrete usage examples — see **[ntj_fconvert_man.md](ntj_fconvert_man.md)**.