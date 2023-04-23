<p align="center">
  <img width="180" src="./BTIPZ.png" alt="Simple Price Tracking Bot">
  <h1 align="center">GeckoTerminal Liquidity and Price Tracking</h1>
</p>

<!-- Table of Contents -->

<summary><h2 style="display: inline-block">Table of Contents</h2></summary>
<ul>
    <li><a href="#intro">Intro</a></li>
    <li><a href="#our-discord">Our Discord</a></li>
    <li><a href="#setup">Setup</a></li>
    <li><a href="#contributing">Contributing</a></li>
    <li><a href="#credit-and-thanks-to">Credit and thanks to</a></li>
</ul>

### Intro

Easy-to-run price name and status for a Discord Bot using GeckoTerminal API.

![Screenshot](https://github.com/0xBTIPZ/Liqudity-and-Token-Price-Discord/blob/main/images/token_transfer.jpg?raw=true)

### Our Discord

* BTIPZ: <http://join.btipz.com>

## Setup

You need to create a Bot through [Discord Application](https://discord.com/developers/applications). You need to run with either python3.8 or python3.10 with virtualenv.

* Copy `config.toml.sample` to `config.toml` and edit as necessary
* Create database in MariaDB / MySQL and import `database.sql`

```
virtualenv -p /usr/bin/python3.10 ./
source bin/activate
pip3 install discord aiohttp aiomysql
python3 geckoterminal_price_btipz.py
```

If you run with pm2 (process monitor):

```
pm2 start `pwd`/geckoterminal_price_btipz.py --name "LPBot-BTIPZ" --interpreter=python3.10
```

Feel free to join [our Discord](http://join.btipz.com) if you need to run your own and has any issue.

## Contributing

Please feel free to open an issue for any suggestions.

### Credit and thanks to:

* <https://api.geckoterminal.com/docs/index.html> GeckoTerminal API.