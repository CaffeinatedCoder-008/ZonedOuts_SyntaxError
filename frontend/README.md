# InSorta frontend (static)

React + Tailwind. It is built into plain files that Flask serves, so the server needs no Node.

```bash
cd frontend
npm install
npm run dev      # http://localhost:5173, needs Flask running on 127.0.0.1:5000
npm run build    # writes ../backend/static  (commit that folder, then deploy)
```

- Data layer: `src/inbox.ts` (calls `/gmail/inbox`, maps categories and deadlines)
- The page: `src/App.tsx`
- Colours / dark mode: `src/global.css`

Always run `npm run build` and commit `backend/static` before deploying.
