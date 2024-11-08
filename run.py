from app import create_app

app = create_app()
# In app.py or your main application file
from app.auth import auth  # Adjust the import based on your structure
app.register_blueprint(auth, url_prefix='/auth')

if __name__ == '__main__':
    app.run(debug=True)
