# README #

Use the setup.txt in clients/ to install this version to a raspberry pi.

For the router, put the clients/nginx.conf to the /etc/nginx directory as
nginx.conf and put clients/blastrouter/nginx.router.conf in
/etc/nginx/sites-available.
Run "sudo ln -s /etc/nginx/sites-available/nginx.router.conf /etc/nginx/sites-enabled/router"
(maybe remove the /etc/nginx/sites-enabled/default first) and "sudo service nginx restart".

Run the file through the ssh shell. "./blastrouter.py" if your in the directory of the file.

Now you can start clients to register them selfs with the router.

There are 2 setups, one for scheduled pwm and one just turning on the led.
    1. You can start the clients/blastclient/blastactuator.py file on the
       raspberries and control it with the controller/blastcontrol.py from your
       local computer
    2. You can start the clients/blastclient/scheduled_leds.py file on the
       raspberries and control it with the controller/scheduled_control.py from
       your local computer

The control will ask for the hostname of the raspberry that you want to control,
in my case it is "automata1" and "automata2".


### What is this repository for? ###

* Raspberry pin pwm control through websockets
* 0.0.1
