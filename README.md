# ml-cards on Cloudflare (Different Account)

This folder is a static site. It depends on the Worker in `personal-cf-workers/ml-cards-worker` for view counting.

## 1) Prepare target Cloudflare account

Create an API token in the target account with permissions for:

- Workers Scripts: Edit
- Workers KV Storage: Edit
- Account: Read
- Cloudflare Pages: Edit

Then set environment variables in your terminal:

```bash
export CLOUDFLARE_API_TOKEN="<target-account-api-token>"
export CLOUDFLARE_ACCOUNT_ID="<target-account-id>"
```

## 2) Deploy Worker in target account

```bash
cd ../personal-cf-workers/ml-cards-worker
npm install
```

Create a new KV namespace in the target account:

```bash
npx wrangler kv namespace create CARD_VIEWS
```

Copy the returned namespace id into `wrangler.toml` as `[[kv_namespaces]].id`.

Deploy the Worker:

```bash
npx wrangler deploy
```

After deploy, note your new Worker URL, for example:

```text
https://ml-cards-worker.<target-subdomain>.workers.dev
```

## 3) Point frontend to the new account

Edit `config.js` in this folder:

- Set `workerUrl` to the new Worker URL.
- Set `cfBeaconToken` if you use Cloudflare Web Analytics in the target account.
- Optionally set `tiktokWorkerUrl` if needed.

## 4) Deploy static site to Cloudflare Pages

From `personal-cf-workers/ml-cards-worker`, return to this folder:

```bash
cd ../../ml-cards
npx wrangler pages project create ml-cards
npx wrangler pages deploy . --project-name ml-cards --branch main
```

Cloudflare Pages URL will look like:

```text
https://ml-cards.pages.dev
```

## 5) Verify

- Open the Pages URL
- Open a card detail
- Confirm view count appears and increases
- Check browser network calls to `<workerUrl>/view` and `<workerUrl>/views`

## Notes

- This setup is account-independent as long as `CLOUDFLARE_API_TOKEN` and `CLOUDFLARE_ACCOUNT_ID` are set for the target account.
- If you use custom domains, configure them in the target account after deployment.
