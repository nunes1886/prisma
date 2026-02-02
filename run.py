from app import create_app

app = create_app()

if __name__ == '__main__':
    # debug=True permite que o site atualize sozinho quando você mexe no código
    app.run(debug=True)