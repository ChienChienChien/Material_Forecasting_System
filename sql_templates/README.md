# SQL Templates

These files are **generic templates** that describe the source-query shape used by the
portfolio version. They intentionally avoid internal schema names, table names, system
codes, plant names, and company-specific business identifiers.

The executable portfolio pipeline reads CSV files through `getlib.py`. If this project
is adapted to a real environment, replace these templates with environment-specific SQL
inside a private repository only.
