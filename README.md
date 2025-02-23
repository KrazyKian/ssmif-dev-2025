Hello SSMIF team, this is Kian Holden. Here is how you have to run my submission for the Development Challenge

1. Download Docker
2. Run Docker
3. While Docker is running, open the terminal in this directory
4. Then type in "docker-compose up --build frontend backend" and everything will run automatically.
5. You'll seee some logs. The backend will first query Yahoo Finance for all the historical stock price data and store in the database. The frontend will wait for that to finish, and then you will be able to access the app. This data is saved in a docker volume, so you wont have to wait as long on subsequent runs.
6. Open up http://localhost:3000/ to see the submission once the frontend says something like this:

frontend  | ✅ Backend is ready!
frontend  |
frontend  | > app@0.0.0 dev
frontend  | > vite --host
frontend  |
frontend  |
frontend  |   VITE v6.1.1  ready in 397 ms
frontend  |
frontend  |   ➜  Local:   http://localhost:3000/
frontend  |   ➜  Network: http://172.18.0.4:3000/

