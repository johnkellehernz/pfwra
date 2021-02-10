PFWRA
-----

```
git clone https://github.com/wagtail/bakerydemo.git
cd bakerydemo
docker-compose up --build -d
docker-compose run app /venv/bin/python manage.py load_initial_data
docker-compose up
```

The PFWRA site will now be accessible at http://localhost:8000/ and the Wagtail admin interface at http://localhost:8000/admin/.

Log into the admin with the credentials admin / changeme.