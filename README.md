# hicetnunc.xyz open dataset and parsers

[Hic et nunc](http://hicetnunc.xyz) is a new eco-friendly [NFT](https://en.wikipedia.org/wiki/Non-fungible_token) marketplace, built on top of [Tezos](https://en.wikipedia.org/wiki/Tezos) blockchain.

It is especially popular in generative graphics and data viz community, so I've decided to share data and all scripts that I've made for https://hashquine.github.io/hicetnunc rating.

It is published under [CC BY](https://creativecommons.org/licenses/by/2.0/) license, so that it is even possible to sell NFTs that use that data (or modified scripts) as long as there is the following phrase somewhere in the token description: `based on @hashquine dataset`.

Since hic et nunc servers are already under an extreme load due to quick growth, I've reorganized code, so that all data is taken from Tezos blockchain and IPFS **without any calls** to the [hicetnunc.xyz](http://hicetnunc.xyz) website or API. 

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
* `sold_count` &mdash; values count (excl. zeros),
* `sold_zero_count` &mdash; number of zeros,
* `sold_price_min` &mdash; minimum value (excl. zeros),
* `sold_price_max` &mdash; maximum value,
* `sold_price_sum` &mdash; sum of values,
* `sold_price_avg` &mdash; average value (sum divided by count excl. zeros).


### [tokens.json](./dataset/tokens.json) and [tokens.csv](./dataset/tokens.csv) &mdash; of all NFTs tokens

There is a confusing fact, that in hicetnunc each NFT can have multiple identical instances, which are fungible.
In this document term "token" refers to the set of all that instances.

There are following invariants:
<pre>mint_count = author_owns_count + available_count + other_own_count + burn_count
author_sent_count <= other_own_count</pre>

<table><tr>
    <th>field</th>
    <th>type</th>
    <th>example</th>
    <th>description</th>
</tr><tr>    <td><code>token_id</code></td>
    <td><code>string</code></td>
    <td><code>"152"</code></td>
    <td>Token identifier: numeric strings with OBJKT ids from <code>https://www.hicetnunc.xyz/objkt/{token_id}</code>.</td>
</tr><tr>
    <td><code>creator</code></td>
    <td><code>string</code></td>
    <td><code>"tz1UBZUk..."</code></td>
    <td>Address of the token minter.</td>
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
    <td><code>"tag1    tag2"</code></td>
    <td>List of the NFT tags specified by creator delimited with tab character.</td>
</tr><tr>
    <td colspan="4" align="center"><b>Statistics fields</b></td>
</tr><tr>
    <td><code>author_sold_count</code><br><code>author_sold_zero_count</code><br><code>author_sold_prices_min</code><br><code>author_sold_prices_max</code><br><code>author_sold_prices_sum</code><br><code>author_sold_prices_avg</code></td>
    <td><code>integer</code><br><code>integer</code><br><code>float</code><br><code>float</code><br><code>float</code><br><code>float</code></td>
    <td><code>100</code><br><code>10</code><br><code>1.25</code><br><code>2.5</code><br><code>33.7</code><br><code>1.325</code></td>
    <td>Prices of sold works (in swaps) by author in XTZ. <br><br>Note, that theoretically single NFT instance can be sold by author multiple times in case the buyer returns it back.</td>
</tr><tr>
    <td><code>secondary_sold_count</code><br><code>secondary_sold_zero_count</code><br><code>secondary_sold_prices_min</code><br><code>secondary_sold_prices_max</code><br><code>secondary_sold_prices_sum</code><br><code>secondary_sold_prices_avg</code></td>
    <td><code>integer</code><br><code>integer</code><br><code>float</code><br><code>float</code><br><code>float</code><br><code>float</code></td>
    <td><code>100</code><br><code>10</code><br><code>1.25</code><br><code>2.5</code><br><code>33.7</code><br><code>1.325</code></td>
    <td>Prices of sold works (in swaps) by other users in XTZ.</td>
</tr><tr>
    <td><code>available_count</code><br><code>available_zero_count</code><br><code>available_prices_min</code><br><code>available_prices_max</code><br><code>available_prices_sum</code><br><code>available_prices_avg</code></td>
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
    <td>How much instances were directly transferred by author to users without swaps.</td>
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
    <td>Address of the token creator as specified in token meta JSON file. In 99.99% the same as <code>creator</code> field, but sometimes empty probably due to some bug.</td>
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
    <td>User logo according to <a href="https://github.com/hicetnunc2000/hicetnunc/blob/main/FAQ.md#how-to-get-verified">tzkt.io metadata</a>. Add prefix <code>https://services.tzkt.io/v1/avatars2/{logo}</code> to get the full url</td>
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
    <td colspan="4" align="center"><b>Statistics fields</b></td>
</tr><tr>
    <td><code>bought_count</code><br><code>bought_zero_count</code><br><code>bought_prices_min</code><br><code>bought_prices_max</code><br><code>bought_prices_sum</code><br><code>bought_prices_avg</code></td>
    <td><code>integer</code><br><code>integer</code><br><code>float</code><br><code>float</code><br><code>float</code><br><code>float</code></td>
    <td><code>100</code><br><code>10</code><br><code>1.25</code><br><code>2.5</code><br><code>33.7</code><br><code>1.325</code></td>
    <td>Prices of bought works (in swaps) by this address in XTZ.</td>
</tr><tr>
    <td><code>author_sold_count</code><br><code>author_sold_zero_count</code><br><code>author_sold_prices_min</code><br><code>author_sold_prices_max</code><br><code>author_sold_prices_sum</code><br><code>author_sold_prices_avg</code></td>
    <td><code>integer</code><br><code>integer</code><br><code>float</code><br><code>float</code><br><code>float</code><br><code>float</code></td>
    <td><code>100</code><br><code>10</code><br><code>1.25</code><br><code>2.5</code><br><code>33.7</code><br><code>1.325</code></td>
    <td>Prices of sold works (in swaps) by author in XTZ.</td>
</tr><tr>
    <td><code>secondary_sold_count</code><br><code>secondary_sold_zero_count</code><br><code>secondary_sold_prices_min</code><br><code>secondary_sold_prices_max</code><br><code>secondary_sold_prices_sum</code><br><code>secondary_sold_prices_avg</code></td>
    <td><code>integer</code><br><code>integer</code><br><code>float</code><br><code>float</code><br><code>float</code><br><code>float</code></td>
    <td><code>100</code><br><code>10</code><br><code>1.25</code><br><code>2.5</code><br><code>33.7</code><br><code>1.325</code></td>
    <td>Prices of sold works on secondary market (i.e. swaps not by author) in XTZ.</td>
</tr><tr>
    <td><code>available_count</code><br><code>available_zero_count</code><br><code>available_prices_min</code><br><code>available_prices_max</code><br><code>available_prices_sum</code><br><code>available_prices_avg</code></td>
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
</tr><tr>
    <td colspan="4" align="center"><b>Auxiliary fields</b></td>
</tr><tr>
    <td><code>first_op_has_reveal</code></td>
    <td><code>boolean</code></td>
    <td><code>1</code> <code>0</code></td>
    <td>Whether first interaction with hicetnunc was the first transaction in Tezos for user</td>
</tr></table>

### [sells.json](./dataset/sells.json) and [sells.csv](./dataset/sells.csv) &mdash; of all purchases via swaps

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
    <td><code>is_secondary</code></td>
    <td><code>boolean</code></td>
    <td><code>1</code> <code>0</code></td>
    <td>If 1 - swap was created by other user, so it is the secondary market.</td>
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
    <td><code>author-&gt;swap</code><br><code>swap-&gt;author</code><br><code>swap-&gt;user</code><br><code>user-&gt;user</code><br><code>author-&gt;trash</code><br><code>user-&gt;trash</code><br><code>user-&gt;swap</code></td>
    <td>String, which characterizes transfer in following terms: <code>author</code>, <code>swap</code>, <code>user</code>, <code>trash</code>. <br>This division is a convention used in this repository only.</td>
</tr><tr>
    <td><code>token_id</code></td>
    <td><code>string</code></td>
    <td><code>"207"</code></td>
    <td>Numeric string with token identifier.</td>
</tr><tr>
    <td><code>price</code></td>
    <td><code>float</code></td>
    <td><code>1.5</code></td>
    <td>Price per item in XTZ or 0 for direct transfers.</td>
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
</tr></table>

### [swaps.json](./dataset/swaps.json) and [swaps.csv](./dataset/swaps.csv) &mdash; all swaps ever created

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
    <td><code>is_secondary</code></td>
    <td><code>boolean</code></td>
    <td><code>1</code> <code>0</code></td>
    <td>If 1 - swap was created by other user, so it is the secondary market.</td>
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

