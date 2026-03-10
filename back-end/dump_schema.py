from app import create_app, db
app = create_app()

with app.app_context():
    from sqlalchemy.schema import CreateTable
    ddl = []
    for table_name, table in db.metadata.tables.items():
        create_stmt = CreateTable(table).compile(db.engine)
        ddl.append(str(create_stmt))
    with open('schema.sql', 'w') as f:
        f.write(';\n'.join(ddl) + ';')
