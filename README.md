# hicetnunc.xyz open dataset and parsers

<a href="https://creativecommons.org/licenses/by/4.0/"><img src="https://img.shields.io/badge/license-CC%20BY-green" /></a> <img src="https://img.shields.io/badge/python-3.6-yellow"/> <a href="https://hub.docker.com/repository/docker/pallada92/hicetnunc-dataset"><img src="https://img.shields.io/badge/docker%20hub-pallada92%2Fhicetnunc--dataset-blue" /></a>

[Hic et nunc](http://hicetnunc.xyz) is a new eco-friendly [NFT](https://en.wikipedia.org/wiki/Non-fungible_token) marketplace, built on top of [Tezos](https://en.wikipedia.org/wiki/Tezos) blockchain.

It is especially popular in generative graphics and data viz community, so I've decided to share data and all scripts that I've made for https://hashquine.github.io/hicetnunc rating.

It is published under [CC BY](https://creativecommons.org/licenses/by/4.0/) license, so that it is even possible to sell NFTs that use that data (or modified scripts) as long as there is the following phrase somewhere in the token description: `based on @hashquine dataset`.

Since hicetnunc servers are already under an extreme load due to quick growth, I've reorganized code, so that all data is taken from Tezos blockchain and IPFS **without any calls** to the [hicetnunc.xyz](http://hicetnunc.xyz) website or API. 

## Data sources

* Blockchain transactions by [TzStats API](https://tzstats.com/docs/api#tezos-api) ([better-call.dev](https://better-call.dev) was not used in order not to interfere with hicetnunc backend).
* [IPFS](https://ru.wikipedia.org/wiki/IPFS) by [cloudflare-ipfs.com](https://cloudflare-ipfs.com/) and [ipfs.io](https://ipfs.io/) depending on mime type (same sources as in hicetnunc frontend).
* Wallet address owner metadata (name, Twitter etc.) from [api.tzkt.io](https://api.tzkt.io/#operation/Accounts_GetMetadata) (same source as in hicetnunc frontend).

## What data is available

* Money data: list of all purchases, prices and commissions.
* All NFTs raw files, their previews and thumbnails, although 3d files and interactive SVG/HTML files are not yet processed properly.
* Authors metadata [verified via tzkt.io](https://github.com/hicetnunc2000/hicetnunc/blob/main/FAQ.md#how-to-get-verified) like Twitter account address.
* Token transfers: list of changes of tokens owners including burns and direct transfers.
* All metadata available for tokens.
* Swaps and mints.

Data not available:
* Everything connected with [hDAO tokens](https://github.com/hicetnunc2000/hicetnunc/blob/main/FAQ.md#what-are-those-little-circles-on-each-post-hdao-what-is-that) and [hDAO feed](https://www.hicetnunc.xyz/hdao). Although all related transactions are already being collected, they are not analysed yet.
* Twitter statistics like the number of followers.
* Direct money transfers between users, when NFT tokens are not transferred in the same transaction.

## Dataset schema

The goal was to simplify data analysis and visualization with a wide range of existing tools, so there are lots of redundant fields, which contain precalculated aggregations and different representations of the same data.

All files have two equivalent versions: JSON and CSV.
* JSON files are dictionary of dictionaries with rows of CSV files are indexed by the `*_id` field.
* CSV files have commas as delimiters.
* Fields values are ether numbers or strings, empty values represented by `-1` or `""`.
* All identifiers are strings.

Any field, which references some event in the blockchain (for example, mint time) have 4 representations:
* `mint_iso_date` &mdash; string with UTC date and time: `"2021-03-01T15:00:00Z"`,
* `mint_stamp` &mdash; integer Unix timestamp in seconds: `1614610800`,
* `mint_hash` &mdash; string with transaction hash, where event occurred: `"oom5Ju6X9nYpBCi..."`,
* `mint_row_id` &mdash; integer with global unique operation id (internal to TzStats) with that event: `42181049`

Any field, which references a set of values (like the set of prices of sold works), have following aggregations:
* `sold_count` &mdash; values count,
* `sold_nonzero_count` &mdash; number of positive values,
* `sold_zero_count` &mdash; number of zeros,
* `sold_price_min` &mdash; minimum value (excl. zeros),
* `sold_price_max` &mdash; maximum value,
* `sold_price_sum` &mdash; sum of values,
* `sold_price_avg` &mdash; average value (sum divided by count excl. zeros).


### [tokens.json](./dataset/tokens.json) and [tokens.csv](./dataset/tokens.csv) &mdash; of all NFTs tokens

There is a confusing fact, that in hicetnunc each NFT can have multiple identical instances, which are fungible.
In this document term "token" refers to the set of all that instances.

There are following invariants:
<pre>mint_count = author_owns_count + available_count + available_zero_count + other_own_count + burn_count
author_sent_count <= other_own_count + available_count + available_zero_count</pre>

<table><tr>
    <th>field</th>
    <th>type</th>
    <th>example</th>
    <th>description</th>
</tr><tr>    <td><code>token_id</code></td>
    <td><code>string</code></td>
    <td><code>"152"</code></td>
    <td>Token identifier: numeric strings with OBJKT ids from <code>hicetnunc.xyz/objkt</code> url.</td>
</tr><tr>
    <td><code>issuer</code></td>
    <td><code>string</code></td>
    <td><code>"tz1UBZUk..."</code></td>
    <td>Address of the person, who intiated mint transaction and receives royalties. It is also referred to as token author in this dataset.</td>
</tr><tr>
    <td><code>mint_count</code></td>
    <td><code>integer</code></td>
    <td><code>100</code></td>
    <td>How many token instances were minted. This number does not change: it is impossible to mint additional token instances in hicetnunc for now.</td>
</tr><tr>
    <td><code>mint_iso_date</code><br><code>mint_stamp</code><br><code>mint_hash</code><br><code>mint_row_id</code></td>
    <td><code>string</code><br><code>integer</code><br><code>string</code><br><code>integer</code></td>
    <td><code>"2021-03-01T15:00:03Z"</code><br><code>1614610803</code><br><code>"oom5Ju6X9nYpBCi..."</code><br><code>42181049</code></td>
    <td>Mint event.</td>
</tr><tr>
    <td><code>artifact_ipfs</code></td>
    <td><code>string</code></td>
    <td><code>"Qma11k..."</code></td>
    <td>IPFS address of NFT content.</td>
</tr><tr>
    <td><code>artifact_mime</code></td>
    <td><code>string</code></td>
    <td><code>"image/gif"</code></td>
    <td>Mime type of <code>artifact_ipfs</code>.</td>
</tr><tr>
    <td><code>artifact_file_size</code></td>
    <td><code>integer</code></td>
    <td><code>2043418</code></td>
    <td>File size of <code>artifact_ipfs</code> in bytes.</td>
</tr><tr>
    <td><code>artifact_preview_width</code></td>
    <td><code>integer</code></td>
    <td><code>1024</code></td>
    <td>Preview image width of <code>artifact_ipfs</code> in pixels. Not more, than 1024.</td>
</tr><tr>
    <td><code>artifact_preview_height</code></td>
    <td><code>integer</code></td>
    <td><code>781</code></td>
    <td>Preview image height of <code>artifact_ipfs</code> in pixels. Not more, than 1024.</td>
</tr><tr>
    <td><code>info_title</code></td>
    <td><code>string</code></td>
    <td><code>"Dali tower"</code></td>
    <td>Title of the NFT specified by creator.</td>
</tr><tr>
    <td><code>info_description</code></td>
    <td><code>string</code></td>
    <td><code>"generated by ..."</code></td>
    <td>Description of the NFT specified by creator.</td>
</tr><tr>
    <td><code>info_tags</code></td>
    <td><code>string</code></td>
    <td><code>"tag1 tag2"</code></td>
    <td>List of the NFT tags specified by creator delimited with space character.</td>
</tr><tr>
    <td><code>ban_status</code></td>
    <td><code>string</code></td>
    <td><code>"banned"</code></td>
    <td>If empty - token is ok, <code>banned</code> - token is banned, <code>author_banned</code> - token author is banned. Ban status is taken from <a href="https://github.com/hicetnunc2000/hicetnunc/tree/main/filters" target="_blank">hicetnunc repository</a></td>
</tr><tr>
    <td colspan="4" align="center"><b>Statistics fields</b></td>
</tr><tr>
    <td><code>author_sold_count</code><br><code>author_sold_nonzero_count</code><br><code>author_sold_zero_count</code><br><code>author_sold_prices_min</code><br><code>author_sold_prices_max</code><br><code>author_sold_prices_sum</code><br><code>author_sold_prices_avg</code></td>
    <td><code>integer</code><br><code>integer</code><br><code>float</code><br><code>float</code><br><code>float</code><br><code>float</code></td>
    <td><code>100</code><br><code>10</code><br><code>1.25</code><br><code>2.5</code><br><code>33.7</code><br><code>1.325</code></td>
    <td>Prices of sold works (in swaps) by author in XTZ. <br><br>Note, that theoretically single NFT instance can be sold by author multiple times in case the buyer returns it back.</td>
</tr><tr>
    <td><code>secondary_sold_count</code><br><code>secondary_sold_nonzero_count</code><br><code>secondary_sold_zero_count</code><br><code>secondary_sold_prices_min</code><br><code>secondary_sold_prices_max</code><br><code>secondary_sold_prices_sum</code><br><code>secondary_sold_prices_avg</code></td>
    <td><code>integer</code><br><code>integer</code><br><code>float</code><br><code>float</code><br><code>float</code><br><code>float</code></td>
    <td><code>100</code><br><code>10</code><br><code>1.25</code><br><code>2.5</code><br><code>33.7</code><br><code>1.325</code></td>
    <td>Prices of sold works (in swaps) by other users in XTZ.</td>
</tr><tr>
    <td><code>available_count</code><br><code>available_nonzero_count</code><br><code>available_zero_count</code><br><code>available_prices_min</code><br><code>available_prices_max</code><br><code>available_prices_sum</code><br><code>available_prices_avg</code></td>
    <td><code>integer</code><br><code>integer</code><br><code>float</code><br><code>float</code><br><code>float</code><br><code>float</code></td>
    <td><code>100</code><br><code>10</code><br><code>1.25</code><br><code>2.5</code><br><code>33.7</code><br><code>1.325</code></td>
    <td>Prices of available works (in swaps) both from author and on secondary market in XTZ.</td>
</tr><tr>
    <td><code>burn_count</code></td>
    <td><code>integer</code></td>
    <td><code>15</code></td>
    <td>How many token instances were burned by creator or other users.</td>
</tr><tr>
    <td><code>author_owns_count</code></td>
    <td><code>integer</code></td>
    <td><code>5</code></td>
    <td>How many token instances are owned by author (not including <code>available_count</code>).</td>
</tr><tr>
    <td><code>other_own_count</code></td>
    <td><code>integer</code></td>
    <td><code>95</code></td>
    <td>How many token instances are owned by other users (not by burn, swap or author).</td>
</tr><tr>
    <td><code>author_sent_count</code></td>
    <td><code>integer</code></td>
    <td><code>5</code></td>
    <td>How much instances were directly transferred by author to users without official swaps.</td>
</tr><tr>
    <td colspan="4" align="center"><b>Auxiliary fields</b></td>
</tr><tr>
    <td><code>info_ipfs</code></td>
    <td><code>string</code></td>
    <td><code>"Qma11k..."</code></td>
    <td>IPFS identifier of the NFT JSON metadata</td>
</tr><tr>
    <td><code>display_uri_ipfs</code></td>
    <td><code>string</code></td>
    <td><code>"Qma11k..."</code></td>
    <td>Token preview image identifier on IPFS or empty string. Note, that it is rare and only used for specific file types like HTML</td>
</tr><tr>
    <td><code>royalties</code></td>
    <td><code>float</code></td>
    <td><code>10.0</code></td>
    <td>"Royalties" parameter passed during token mint in percent. </td>
</tr><tr>
    <td><code>info_creator</code></td>
    <td><code>string</code></td>
    <td><code>"tz1UBZUk..."</code></td>
    <td>Address of the token creator as specified in token meta JSON file. In 99.99% the same as <code>issuer</code> field, but sometimes empty probably due to some bug.</td>
</tr><tr>
    <td><code>mint_tokens_receiver</code></td>
    <td><code>string</code></td>
    <td><code>"tz1UBZUk..."</code></td>
    <td>Address of the user, who received tokens after mint transaction. In 99% the same as <code>issuer</code> field.</td>
</tr><tr>
    <td><code>mint_ah_row_id</code></td>
    <td><code>integer</code></td>
    <td><code>None</code></td>
    <td>Row id of mint operation by "Art house" contract (not by NFT contract).</td>
</tr></table>

### [addrs.json](./dataset/addrs.json) and [addrs.csv](./dataset/addrs.csv) &mdash; of all hicetnunc users

All users, who ever created or owned NFT token.

<table><tr>
    <th>field</th>
    <th>type</th>
    <th>example</th>
    <th>description</th>
</tr><tr>    <td><code>address</code></td>
    <td><code>string</code></td>
    <td><code>"tz1UBZUk..."</code></td>
    <td>Address of the user in Tezos blockchain. Can be contract address as well.</td>
</tr><tr>
    <td><code>first_action_iso_date</code><br><code>first_action_stamp</code><br><code>first_action_hash</code><br><code>first_action_row_id</code></td>
    <td><code>string</code><br><code>integer</code><br><code>string</code><br><code>integer</code></td>
    <td><code>"2021-03-01T15:00:03Z"</code><br><code>1614610803</code><br><code>"oom5Ju6X9nYpBCi..."</code><br><code>42181049</code></td>
    <td>When first transaction (related to hicetnunc) with this address occurred.</td>
</tr><tr>
    <td><code>tzkt_info_name</code></td>
    <td><code>string</code></td>
    <td><code>"dacosta works"</code></td>
    <td>User alias field according to <a href="https://github.com/hicetnunc2000/hicetnunc/blob/main/FAQ.md#how-to-get-verified">tzkt.io metadata</a>.</td>
</tr><tr>
    <td><code>tzkt_info_twitter</code></td>
    <td><code>string</code></td>
    <td><code>"dacosta_works"</code></td>
    <td>User Twitter account according to <a href="https://github.com/hicetnunc2000/hicetnunc/blob/main/FAQ.md#how-to-get-verified">tzkt.io metadata</a>.</td>
</tr><tr>
    <td><code>tzkt_info_email</code></td>
    <td><code>string</code></td>
    <td><code>"sartist@gmail.com"</code></td>
    <td>User e-mail according to <a href="https://github.com/hicetnunc2000/hicetnunc/blob/main/FAQ.md#how-to-get-verified">tzkt.io metadata</a>.</td>
</tr><tr>
    <td><code>tzkt_info_instagram</code></td>
    <td><code>string</code></td>
    <td><code>"dacosta_works"</code></td>
    <td>User Instagram account according to <a href="https://github.com/hicetnunc2000/hicetnunc/blob/main/FAQ.md#how-to-get-verified">tzkt.io metadata</a>.</td>
</tr><tr>
    <td><code>tzkt_info_site</code></td>
    <td><code>string</code></td>
    <td><code>"https://jsh.sh"</code></td>
    <td>User website according to <a href="https://github.com/hicetnunc2000/hicetnunc/blob/main/FAQ.md#how-to-get-verified">tzkt.io metadata</a>.</td>
</tr><tr>
    <td><code>tzkt_info_description</code></td>
    <td><code>string</code></td>
    <td><code>"NFT artist ..."</code></td>
    <td>User description according to <a href="https://github.com/hicetnunc2000/hicetnunc/blob/main/FAQ.md#how-to-get-verified">tzkt.io metadata</a>.</td>
</tr><tr>
    <td><code>tzkt_info_logo</code></td>
    <td><code>string</code></td>
    <td><code>"huson.png"</code></td>
    <td>User logo according to <a href="https://github.com/hicetnunc2000/hicetnunc/blob/main/FAQ.md#how-to-get-verified">tzkt.io metadata</a>. Add prefix <code>https://services.tzkt.io/v1/avatars2/</code> to get the full url</td>
</tr><tr>
    <td><code>tzkt_info_github</code></td>
    <td><code>string</code></td>
    <td><code>"josim"</code></td>
    <td>User GitHub account according to <a href="https://github.com/hicetnunc2000/hicetnunc/blob/main/FAQ.md#how-to-get-verified">tzkt.io metadata</a>.</td>
</tr><tr>
    <td><code>tzkt_info_telegram</code></td>
    <td><code>string</code></td>
    <td><code>"thebaskia"</code></td>
    <td>User Telegram account according to <a href="https://github.com/hicetnunc2000/hicetnunc/blob/main/FAQ.md#how-to-get-verified">tzkt.io metadata</a>.</td>
</tr><tr>
    <td><code>tzkt_info_facebook</code></td>
    <td><code>string</code></td>
    <td><code>"barbeaucodeart"</code></td>
    <td>User Facebook account according to <a href="https://github.com/hicetnunc2000/hicetnunc/blob/main/FAQ.md#how-to-get-verified">tzkt.io metadata</a>.</td>
</tr><tr>
    <td><code>tzkt_info_reddit</code></td>
    <td><code>string</code></td>
    <td><code>"user/mathmakesart"</code></td>
    <td>User Reddit account according to <a href="https://github.com/hicetnunc2000/hicetnunc/blob/main/FAQ.md#how-to-get-verified">tzkt.io metadata</a>.</td>
</tr><tr>
    <td><code>ban_status</code></td>
    <td><code>string</code></td>
    <td><code>"banned"</code></td>
    <td>If empty - author is ok, <code>banned</code> - user is banned, <code>some_tokens_banned</code> - user is not banned, but it minted banned tokens. Ban status is taken from <a href="https://github.com/hicetnunc2000/hicetnunc/tree/main/filters" target="_blank">hicetnunc repository</a></td>
</tr><tr>
    <td colspan="4" align="center"><b>Statistics fields</b></td>
</tr><tr>
    <td><code>mint_count</code></td>
    <td><code>integer</code></td>
    <td><code>125</code></td>
    <td>Number of minted works.</td>
</tr><tr>
    <td><code>bought_count</code><br><code>bought_nonzero_count</code><br><code>bought_zero_count</code><br><code>bought_prices_min</code><br><code>bought_prices_max</code><br><code>bought_prices_sum</code><br><code>bought_prices_avg</code></td>
    <td><code>integer</code><br><code>integer</code><br><code>float</code><br><code>float</code><br><code>float</code><br><code>float</code></td>
    <td><code>100</code><br><code>10</code><br><code>1.25</code><br><code>2.5</code><br><code>33.7</code><br><code>1.325</code></td>
    <td>Prices of bought works (in swaps) by this address in XTZ.</td>
</tr><tr>
    <td><code>author_sold_count</code><br><code>author_sold_nonzero_count</code><br><code>author_sold_zero_count</code><br><code>author_sold_prices_min</code><br><code>author_sold_prices_max</code><br><code>author_sold_prices_sum</code><br><code>author_sold_prices_avg</code></td>
    <td><code>integer</code><br><code>integer</code><br><code>float</code><br><code>float</code><br><code>float</code><br><code>float</code></td>
    <td><code>100</code><br><code>10</code><br><code>1.25</code><br><code>2.5</code><br><code>33.7</code><br><code>1.325</code></td>
    <td>Prices of sold works (in swaps) by author in XTZ.</td>
</tr><tr>
    <td><code>secondary_sold_count</code><br><code>secondary_sold_nonzero_count</code><br><code>secondary_sold_zero_count</code><br><code>secondary_sold_prices_min</code><br><code>secondary_sold_prices_max</code><br><code>secondary_sold_prices_sum</code><br><code>secondary_sold_prices_avg</code></td>
    <td><code>integer</code><br><code>integer</code><br><code>float</code><br><code>float</code><br><code>float</code><br><code>float</code></td>
    <td><code>100</code><br><code>10</code><br><code>1.25</code><br><code>2.5</code><br><code>33.7</code><br><code>1.325</code></td>
    <td>Prices of sold works on secondary market (i.e. swaps not by author) in XTZ.</td>
</tr><tr>
    <td><code>available_count</code><br><code>available_nonzero_count</code><br><code>available_zero_count</code><br><code>available_prices_min</code><br><code>available_prices_max</code><br><code>available_prices_sum</code><br><code>available_prices_avg</code></td>
    <td><code>integer</code><br><code>integer</code><br><code>float</code><br><code>float</code><br><code>float</code><br><code>float</code></td>
    <td><code>100</code><br><code>10</code><br><code>1.25</code><br><code>2.5</code><br><code>33.7</code><br><code>1.325</code></td>
    <td>Prices of available works (in swaps) both by author and other users in XTZ.</td>
</tr><tr>
    <td><code>in_op_count</code></td>
    <td><code>integer</code></td>
    <td><code>25</code></td>
    <td>Number of incoming transactions</td>
</tr><tr>
    <td><code>out_op_count</code></td>
    <td><code>integer</code></td>
    <td><code>33</code></td>
    <td>Number of outcoming transactions</td>
</tr><tr>
    <td><code>money_received</code></td>
    <td><code>float</code></td>
    <td><code>2.78999</code></td>
    <td>Total volume of XTZ received by address in transactions related to hicetnunc</td>
</tr><tr>
    <td><code>money_sent</code></td>
    <td><code>float</code></td>
    <td><code>10</code></td>
    <td>Total volume of XTZ sent by address in transactions related to hicetnunc</td>
</tr></table>

### [sells.json](./dataset/sells.json) and [sells.csv](./dataset/sells.csv) &mdash; of all purchases via "official" hicetnunc swaps

There is the following invariant:
<pre>price * count = total_royalties + total_comission + total_seller_income</pre>

<table><tr>
    <th>field</th>
    <th>type</th>
    <th>example</th>
    <th>description</th>
</tr><tr>    <td><code>tr_iso_date</code><br><code>tr_stamp</code><br><code>tr_hash</code><br><code>tr_row_id</code></td>
    <td><code>string</code><br><code>integer</code><br><code>string</code><br><code>integer</code></td>
    <td><code>"2021-03-01T15:00:03Z"</code><br><code>1614610803</code><br><code>"oom5Ju6X9nYpBCi..."</code><br><code>42181049</code></td>
    <td>When transaction occurred.</td>
</tr><tr>
    <td><code>token_id</code></td>
    <td><code>string</code></td>
    <td><code>"205"</code></td>
    <td>Numeric string with token identifier.</td>
</tr><tr>
    <td><code>count</code></td>
    <td><code>integer</code></td>
    <td><code>10</code></td>
    <td>Number of token instances transferred.</td>
</tr><tr>
    <td><code>seller</code></td>
    <td><code>string</code></td>
    <td><code>"tz1UBZUk..."</code></td>
    <td>Seller address i.e. user who created the swap</td>
</tr><tr>
    <td><code>buyer</code></td>
    <td><code>string</code></td>
    <td><code>"tz1MwvWa..."</code></td>
    <td>Buyer address</td>
</tr><tr>
    <td><code>price</code></td>
    <td><code>float</code></td>
    <td><code>2.5</code></td>
    <td>Price per item in XTZ (how much buyer payed per item)</td>
</tr><tr>
    <td><code>swap_id</code></td>
    <td><code>string</code></td>
    <td><code>"503"</code></td>
    <td>Numeric string with swap identifier.</td>
</tr><tr>
    <td><code>by_author</code></td>
    <td><code>boolean</code></td>
    <td><code>1</code> <code>0</code></td>
    <td>If 1 - swap was created by author, if 0 - by other user.</td>
</tr><tr>
    <td><code>author</code></td>
    <td><code>string</code></td>
    <td><code>"tz1UBZUk..."</code></td>
    <td>Address of token issuer, which receives royalties.</td>
</tr><tr>
    <td colspan="4" align="center"><b>Statistics fields</b></td>
</tr><tr>
    <td><code>total_royalties</code></td>
    <td><code>float</code></td>
    <td><code>12.75</code></td>
    <td>Author income from royalties (already multiplied by <code>count</code>) for secondary sells and 0 otherwise</td>
</tr><tr>
    <td><code>total_comission</code></td>
    <td><code>float</code></td>
    <td><code>1.3</code></td>
    <td>Comission per item in XTZ. Usually 2.5% of price.</td>
</tr><tr>
    <td><code>total_seller_income</code></td>
    <td><code>float</code></td>
    <td><code>1.3</code></td>
    <td>Seller income (already multiplied by <code>count</code>).</td>
</tr></table>

### [transfers.json](./dataset/transfers.json) and [transfers.csv](./dataset/transfers.csv) &mdash; all token transfers

<table><tr>
    <th>field</th>
    <th>type</th>
    <th>example</th>
    <th>description</th>
</tr><tr>    <td><code>tr_iso_date</code><br><code>tr_stamp</code><br><code>tr_hash</code><br><code>tr_row_id</code></td>
    <td><code>string</code><br><code>integer</code><br><code>string</code><br><code>integer</code></td>
    <td><code>"2021-03-01T15:00:03Z"</code><br><code>1614610803</code><br><code>"oom5Ju6X9nYpBCi..."</code><br><code>42181049</code></td>
    <td>When transaction occurred.</td>
</tr><tr>
    <td><code>category</code></td>
    <td><code>string</code></td>
    <td><code>mint-&gt;author</code><br><code>author-&gt;swap</code><br><code>swap-&gt;author</code><br><code>swap-&gt;user</code><br><code>user-&gt;user</code><br><code>author-&gt;burn</code><br><code>user-&gt;burn</code><br><code>user-&gt;ext</code><br>...</code></td>
    <td>String, which characterizes transfer in following terms: <code>author</code>, <code>swap</code>, <code>user</code>, <code>burn</code>, <code>ext</code>. <br>This division is a convention used in this repository only.</td>
</tr><tr>
    <td><code>token_id</code></td>
    <td><code>string</code></td>
    <td><code>"207"</code></td>
    <td>Numeric string with token identifier.</td>
</tr><tr>
    <td><code>price</code></td>
    <td><code>float</code></td>
    <td><code>1.5</code></td>
    <td>Price per item in XTZ or 0 for direct transfers. For external swaps price is guessed heuristically as half of sum of abolute values of transaction money transers (since each money transaction is counted twice both as incoming and outcoming).</td>
</tr><tr>
    <td><code>count</code></td>
    <td><code>integer</code></td>
    <td><code>5</code></td>
    <td>Number of token instances transferred.</td>
</tr><tr>
    <td><code>swap_id</code></td>
    <td><code>string</code></td>
    <td><code>"523"</code></td>
    <td>Numeric string with swap identifier or empty string if it is a direct transfer.</td>
</tr><tr>
    <td><code>sender</code></td>
    <td><code>string</code></td>
    <td><code>"tz1UBZUk..."</code></td>
    <td>Sender address or empty string in case of mint</td>
</tr><tr>
    <td><code>receiver</code></td>
    <td><code>string</code></td>
    <td><code>"tz1MwvWa..."</code></td>
    <td>Receiver address</td>
</tr><tr>
    <td><code>method</code></td>
    <td><code>string</code></td>
    <td><code>"mint_OBJKT"</code></td>
    <td>Called method of hicetnunc or external contract, otherwise empty string</td>
</tr></table>

### [swaps.json](./dataset/swaps.json) and [swaps.csv](./dataset/swaps.csv) &mdash; all "official" hicetnunc swaps ever created

<table><tr>
    <th>field</th>
    <th>type</th>
    <th>example</th>
    <th>description</th>
</tr><tr>    <td><code>swap_id</code></td>
    <td><code>string</code></td>
    <td><code>"503"</code></td>
    <td>Numeric string with swap identifier.</td>
</tr><tr>
    <td><code>token_id</code></td>
    <td><code>string</code></td>
    <td><code>"207"</code></td>
    <td>Numeric string with token identifier.</td>
</tr><tr>
    <td><code>price</code></td>
    <td><code>float</code></td>
    <td><code>1.5</code></td>
    <td>Price per item in XTZ.</td>
</tr><tr>
    <td><code>total_count</code></td>
    <td><code>integer</code></td>
    <td><code>100</code></td>
    <td>Total number of instances in swap.</td>
</tr><tr>
    <td><code>created_iso_date</code><br><code>created_stamp</code><br><code>created_hash</code><br><code>created_row_id</code></td>
    <td><code>string</code><br><code>integer</code><br><code>string</code><br><code>integer</code></td>
    <td><code>"2021-03-01T15:00:03Z"</code><br><code>1614610803</code><br><code>"oom5Ju6X9nYpBCi..."</code><br><code>42181049</code></td>
    <td>When swap was created.</td>
</tr><tr>
    <td><code>closed_iso_date</code><br><code>closed_stamp</code><br><code>closed_hash</code><br><code>closed_row_id</code></td>
    <td><code>string</code><br><code>integer</code><br><code>string</code><br><code>integer</code></td>
    <td><code>"2021-03-01T15:00:03Z"</code><br><code>1614610803</code><br><code>"oom5Ju6X9nYpBCi..."</code><br><code>42181049</code></td>
    <td>When swap was closed (cancelled). If closed, swap cannot be reopened again.</td>
</tr><tr>
    <td><code>by_author</code></td>
    <td><code>boolean</code></td>
    <td><code>1</code> <code>0</code></td>
    <td>If 1 - swap was created by author, if 0 - by other user.</td>
</tr><tr>
    <td><code>created_by</code></td>
    <td><code>string</code></td>
    <td><code>"tz1UBZUk..."</code></td>
    <td>Address of the user, which created swap.</td>
</tr><tr>
    <td colspan="4" align="center"><b>Statistics fields</b></td>
</tr><tr>
    <td><code>sold_count</code></td>
    <td><code>integer</code></td>
    <td><code>99</code></td>
    <td>Number of sold (including with zero price) instances.</td>
</tr><tr>
    <td><code>available_count</code></td>
    <td><code>integer</code></td>
    <td><code>1</code></td>
    <td>Number of available instances if the swap is not closed, 0 otherwise.</td>
</tr><tr>
    <td><code>returned_count</code></td>
    <td><code>integer</code></td>
    <td><code>0</code></td>
    <td>Number of unsold instances returned to the swap creator if the swap was closed, 0 otherwise.</td>
</tr><tr>
    <td><code>sold_price_sum</code></td>
    <td><code>float</code></td>
    <td><code>148.5</code></td>
    <td>Total price of sold instances in XTZ.</td>
</tr></table>

## Essential information about contracts logic

There are 3 Tezos addresses, which are common to most of hicetnunc transactions:

* **"NFT" contract**: [KT1RJ6PbjHpwc3M5rw5s2Nbmefwbuwbdxton](https://tzstats.com/KT1RJ6PbjHpwc3M5rw5s2Nbmefwbuwbdxton).
    * This is the registry of all owners of all NFT tokens.
        * This is the typical way how most of NFTs works on Ethereum or on Tezos.
        * Click on "Bigmap #511" tab in Tezos explorer to see registry of token owners.
        * This contract is the single "source of truth" about current owners of all NFT tokens issued by hicetnunc.
          If there is no information about token owner in the registry, than that person doesn't own any tokens.
    * This contract also the registry of tokens infos (metadata).
        * Token info is a small JSON structure stored on on IPFS.
            * [Here is an example](https://ipfs.tzstats.com/ipfs/Qme3LXQF2UaqCx1ksDtHSSFTmuER8AehoayHKoTvfT9rQ6) of such structure.
            * It contains link to IPFS with NFT binary contents (some image, for example).
            * It also contains title, description, creator and tags.
            * It **does not** contain price or related information.
        * Only link to IPFS is stored on the blockchain.
        * Note, that, however, there is no way to alter token metadata after minting.
        * Click on "Bigmap #514" tab in Tezos explorer to see mapping from tokens to IPFS urls.
    * Every token owner can call "transfer" method of the contract to send tokens to other address.
        * This contract can't do any money related operations.
          Money logic should be implemented in other contracts, which call "NFT" contract as a part of transaction operation.
    * There is also a "mint" method in this contract, but it can only be called by the "Art house" contract.
* **"Art house" contract**: [KT1Hkg5qeNhfwpKW4fXvq7HGZB9z2EnmCCA9](https://tzstats.com/KT1Hkg5qeNhfwpKW4fXvq7HGZB9z2EnmCCA9).
    * This contract implements money related operations on hicetnunc.
    * It's main structure is a swap. It is some amount of tokens, which are available of sale for specific price.
        * Click on "Bigmap #523" tab in Tezos explorer to see all current swaps.
    * Note, that there may be other contracts implementing swap mechanism. These contracts may decide not to pay comission or royalties.
    * Objects can be minted only with this contract by calling "mint_OBJKT" method.
        * This contract keeps track of royalties and assigns tokens ids.
* **Comission wallet:** [tz1UBZUkXpKGhYsP5KtzDNqLLchwF4uHrGjw](https://tzstats.com/tz1UBZUkXpKGhYsP5KtzDNqLLchwF4uHrGjw).
    * 2.5% of every purchase via "Art house" contract swaps is sent to this wallet.

There are several other contracts related to [curation](https://tzstats.com/KT1TybhR7XraG75JFYKSrh7KnxukMBT5dor6) and [hDAO](https://tzstats.com/KT1AFA2mwNUMNd4SsujE1YYp29vd8BZejyKW) mechanisms, which are independent from the contracts mentioned above.

Actually, hicetnunc was not created just as another NFT marketplace, it has much broader mission as hDAO (hicetnunc [DAO](https://en.wikipedia.org/wiki/The_DAO_(organization))). You can get the idea of the creators vision [on hicetnunc blog](https://hicetnunc2000.medium.com/). As a result, only a small subset of contract's logic is actually used during hicetnunc website operation.

### Official and external swap mechanisms

* Official swap mechanism by hicetnunc "Art house" contract.
    * Any token bought on hicetnunc website is a part of some swap.
    * Swap is just some amount of tokens, which are offered for sale by specific price.
    * When swap is created, the seller sends all offered tokens to the "Art house" smart contract.
    * Then anybody can send the required amount of money to the "collect" method of contract and get tokens in return.
        * 2.5% of comission is transferred to hicetnunc comission wallet.
        * 10% of royalties (this parameter is configurable in general) is transferred to token author.
        * rest of money is sent to swap creator.
        * proportional amount of hDAO tokens are also sent to buyer, seller, token author and comission wallet.
    * Seller can cancel swap any time and get unsold tokens back.
    * Swaps can be created by any token owner any number of times.
    * In this dataset official swaps are treated as `author->swap`, `other->swap`, `swap->author`, `swap->other` transfers.

* External swap mechanisms.
    * Since "transfer" method of "NFT" contract can be called by any token owner directly, it is possible to make custom smart contracts, which implement any desired logic.
    * These custom contracts are not required not pay comission or royalties to hicetnunc.
    * In general, swap contracts can be used to exchange any types entities.
    * Example: https://quipuswap.com/swap
    * In this dataset external swaps are treated as `other->other` transfers. The related price is guessed heuristically (as half of money transferred in all operations) and may not be always correct.

### Token lifecycle

In contrast to NFT definition, each NFT artwork in hicetnunc can have multiple copies, which are fungible. The NFT contract only tracks the amount of copies owned by each address. This means, that there is no way (even in theory) to track history of single copy like [it can be done on OpenSea](https://opensea.io/assets/0x06012c8cf97bead5deae237070f9587f8e7a266d/1864227), for example.

It is possible, however, to track history of token groups to some extent. Here is a list of possible owner types in this dataset:

* `author` &mdash; the person, who created the tokens during mint.
* `user` &mdash; any other hicetnunc user.
* `ext` &mdash; any external contract (external swap mechanism, for example).
* `burn` &mdash; reserved address for burning tokens.
* `swap` &mdash; when tokens are offered on sale in official swaps.

List of possible transitions:

* `mint->author`, `mint->user` First, every token should be minted.
    * For each token type there may exist only single mint operation. It is impossible to mint additional tokens later.
    * The only way to mint a token is to call "mint_OBJKT" method in "Art house" contract.
    * [Here is](https://tzstats.com/ooVQqSXkhKHKi6ZDbT5tUxftLYNvC3zpuPrb8qWBEyjwy1hASLv) a typical mint transaction
    * Internally it calls "mint" method in "NFT" contract.
    * In dataset the sender is empty for mint operations.
    * As result of mint operation, all tokens are transferred to some address. In 99% of cases this is the transaction sender, but sometimes it is different.
    * Royalties are always sent to the mint transaction sender.
* `author->swap`, `user->swap` Any token owner can create official swap.
    * Hicetnunc swap is created by calling "swap" method in "Art house" contract.
    * [Here is](https://tzstats.com/opYXNWa6Cs8LoFvsguVpKocmQ6JpksSuTRWcACSfCkuY4UTNkhC) a typical swap creation transaction by author.
    * Internally tokens are transferred to the "Art house" address.
* `swap->author`, `swap->other` There are two situations, when tokens may be transferred from a swap.
    1. Purchase
        * When token is purchased on hicetnunc website, it is transferred to the buyer. This is the main operation on hicetnunc.
        * Buyer should call "collect" method of "Art house" contract and send required amount of money with it.
        * [Here is](https://tzstats.com/op7ft9rqdYvbctZ5NFw2wPDmioBx29nPREgeZgxmdypxL5nxyAk) an example of "collect" transaction.
            * First 3 internal operations send money to token creator (royalties), hicetnunc wallet (comission) and to the seller (which is the same as token creator in some cases) in that order.
            * Fourth operation creates hDAO tokens and sends them to the buyer, seller and hicetnunc wallet. These tokens have special meaning and are not tracked in this dataset.
            * Last internal operation does the actual token transfer.
        * Note, that case of zero price is handled differently.
            * [Here is](https://tzstats.com/ooKbTDkkT9fHoXxrkN5cAEFfbrXnd47YZuGHR991YzEtqneeGrQ) an example of purchase with zero price.
    2. Swap cancel
        * When swap creator decides to cancel swap, all remaining tokens are transferred back to him.
* `author->user`, `user->user` Any token owner can transfer tokens directly to other users for free by calling "transfer" method of "NFT" contract.
    * [Here is](https://tzstats.com/ooDEeiWKwk7eL4DgUELErf6qkycYisbehWZsU3R1M2XWA5DKW2P) an example of direct transfer transaction from author to other user.
* `author->ext`, `user->ext`, `ext->user`, `ext->author` &mdash; external swaps
    * [Here is](https://tzstats.com/ooF1bszbutpvvb5LWrcmd5A1WoqSKGicB2wr7SsVruKbWoaDasD) an example of external swap.
* `author->burn`, `other->burn` Any token owner can transfer tokens to burn address <code>tz1burnburnburnburnburnburnburjAYjjX</code>.
    * [Here is](https://tzstats.com/ooDEeiWKwk7eL4DgUELErf6qkycYisbehWZsU3R1M2XWA5DKW2P) and example of burn transfer from author.
    * Tokens can never be transferred from burn address since it is impossible to retrieve its private key (similar to how it is impossible to reverse hash containing all zeros).


## Details about edge cases 

### How to define the author of the token

1. `mint_sender` The address of the sender of the "mint" transaction.
    * This is the person, who receives royalties in hicetnunc.
    * In this dataset token author this is equivalent to token author.
2. `issuer` The address of the receiver of tokens after the mint transaction.
    * It is also the first parameter of the "mint" call in "Art house" contract.
    * [Here is](https://tzstats.com/ooVQqSXkhKHKi6ZDbT5tUxftLYNvC3zpuPrb8qWBEyjwy1hASLv) an example of mint, where transaction sender and token issuer are different.
3. `info_creator` Field "creators" in JSON in token metadata.
    * [Here is](https://tzstats.com/onu5q4QMQRFD7NsFDWjk5WaeBk8PR2orHhmN6M7qntaTFyMGjJD) an example of mint, where metadata creator field is different from transaction sender and issuer.
    * As of 4th of April, it always has single entry.
    * Sometimes it is empty.
        * [Here is](https://tzstats.com/op8uvfPYcy1Yofn9eCgjrfNvFJkpZfjT6wpP8yezczXxPJcc8Pa) an example of mint with empty metadata creator field.
        * Note, that [corresponding token page](https://www.hicetnunc.xyz/objkt/12123) has a bug, that it shows token owner controls on token page.

### Hicetnunc core addresses can own NFTs as regular users

* Any user can send any NFT tokens to "NFT" or "Art house contract"
    * Technically, it has the same effect as sending this tokens to burn address, since contracts were not programmed to send their own NFTs (except from swap mechanism) under any circumstances.
* Comission wallet sometimes mint NFTs and buys them from other users.
    * Since it is not a contract and manipulated by a real person (hicetnunc creator).

### Void transactions

* It is possible to send 0 tokens. [Example](https://tzstats.com/ooXTr2AJBN95EiN3u7NcUg5K7Pkd8nRHNRxa8CbxRNhQZEW4QLN).
* Sender and receiver can be the same. [Example](https://tzstats.com/opUVg6edpbHtJ94VgHTcwbDnodoegKKwmQ8C6iC9avVX6vZPQd4)


## How to update dataset

Note, that the code is still experimental and may require substantial changes to make it run. But you can read introduction in [HACKING.md](./HACKING.md)