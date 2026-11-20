// Sends .output/public to Firebase Hosting (ARCHITECTURE.md §13). Bun loads viewer/.env into process.env,
// but does not expand its variables in package.json scripts — hence this script instead of `--project $VAR` there.
const project = process.env.FIREBASE_PROJECT_ID?.trim()
if (!project) {
  console.error('deploy: brak FIREBASE_PROJECT_ID w viewer/.env (szablon: .env.example)')
  process.exit(1)
}
const proc = Bun.spawn(['bunx', 'firebase', 'deploy', '--project', project, '--only', 'hosting'], { stdio: ['inherit', 'inherit', 'inherit'] })
process.exit(await proc.exited)
