sudo cp misc/health-recorder.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl restart health-recorder
sudo systemctl status health-recorder
