# hicetnunc.xyz dataset and parsers

[Hic et nunc](http://hicetnunc.xyz) is a new eco-friendly [NFT](https://en.wikipedia.org/wiki/Non-fungible_token) marketplace, built on top of [Tezos](https://en.wikipedia.org/wiki/Tezos) blockchain.

It is especially popular in generative graphics and data viz community, so I've decided to share data and all scripts that I've made for https://hashquine.github.io/hicetnunc rating.

It is published under [CC BY](https://creativecommons.org/licenses/by/2.0/) license, so that it is even possible to sell NFTs that use that data (or modified scripts) as long as there is the following phrase somewhere in the token description: `based on @hashquine dataset`.

Since hic et nunc servers are already under an extreme load due to quick growth, I've reorganized code, so that all data is taken from Tezos blockchain and IPFS **without any calls** to the [hicetnunc.xyz](http://hicetnunc.xyz) website or API. 

## Data sources

* Blockchain transactions by [TzStats API](https://tzstats.com/docs/api#tezos-api) ([better-call.dev](https://better-call.dev) was not used in order not to interfere with hicetnunc backend).
* [IPFS](https://ru.wikipedia.org/wiki/IPFS) by [cloudflare-ipfs.com](https://cloudflare-ipfs.com/) and [ipfs.io](https://ipfs.io/) depending on mime type (same sources as in hicetnunc frontend).
* Wallet address owner metadata (name, Twitter etc.) from [api.tzkt.io](https://api.tzkt.io/#operation/Accounts_GetMetadata) (same source as in hicetnunc frontend).

## Dataset schema

### Tokens

In hicetnunc each NFT can have multiple identical instances, which are fungible.

[tokens.json](./dataset/tokens.json) and [tokens.json](./dataset/tokens.csv) &mdash; all NFTs indexed by `token_id` as string.

| field | type |
|-------|------|
| `token_id` | `number` |

* [tokens.json](./dataset/tokens.json) and [tokens.json](./dataset/tokens.csv) &mdash; all NFTs indexed by ids.
