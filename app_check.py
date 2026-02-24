from app import create_app

app = create_app()

print('=== Registered Routes ===')
for rule in sorted(app.url_map.iter_rules(), key=lambda r: r.rule):
    print(f'{rule.rule}  [{" ".join(rule.methods)}]')

print('\nApp startup: OK')
