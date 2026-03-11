# Setup del VPS para Deploy Automático

## 1. Configurar SSH

En el VPS:

```bash
# Generar clave SSH para deploys
ssh-keygen -t ed25519 -C "github-deploy" -f ~/.ssh/github_deploy -N ""

# Agregar al authorized_keys
cat ~/.ssh/github_deploy.pub >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys

# Copiar la clave privada (para GitHub Secrets)
cat ~/.ssh/github_deploy
```

## 2. Configurar GitHub Secrets

En el repositorio → Settings → Secrets and variables → Actions, agregar:

| Secret | Valor |
|--------|-------|
| `VPS_SSH_KEY` | Contenido completo de `~/.ssh/github_deploy` (clave privada) |
| `VPS_HOST` | IP o dominio del VPS |
| `VPS_USER` | Usuario SSH del VPS |
| `VPS_DEPLOY_PATH` | Ruta absoluta al repo en el VPS (ej: `/opt/consul_app`) |

## 3. Crear directorios de backup

```bash
sudo mkdir -p /opt/backups/consul_app/auto
sudo mkdir -p /opt/backups/consul_app/manual
sudo chown -R $(whoami):$(whoami) /opt/backups/consul_app
```

## 4. Configurar cron para backup semanal

```bash
crontab -e
```

Agregar (viernes a las 21:00):

```
0 21 * * 5 /ruta/al/repo/scripts/backup-db.sh auto /ruta/al/repo >> /var/log/consul_backup.log 2>&1
```

Reemplazar `/ruta/al/repo` con la ruta real (ej: `/opt/consul_app`).

## 4b. Configurar cron para notificaciones de cumpleanos

Agregar al crontab (todos los dias a las 08:00):

```
0 8 * * * cd /ruta/al/repo && make notify-birthdays >> /var/log/consul_notify.log 2>&1
```

Esto envia push notifications a los profesionales que tienen pacientes con cumpleanos ese dia.

## 5. Configurar git remote

El repo está clonado por HTTPS. Cambiar a SSH para que `git pull` no pida credenciales:

```bash
cd /ruta/al/repo
git remote set-url origin git@github.com:mateoadann/consul_app.git
```

Alternativa (mantener HTTPS con token):

```bash
# Configurar credential store
git config --global credential.helper store

# El próximo git pull pedirá usuario y Personal Access Token
# Se guarda automáticamente para futuros pulls
```

## 6. Verificar

```bash
# Probar SSH desde el VPS a GitHub
ssh -T git@github.com

# Probar git pull
cd /ruta/al/repo
git pull origin main

# Probar backup manual
bash scripts/backup-db.sh manual /ruta/al/repo

# Verificar que el backup se creó
ls -la /opt/backups/consul_app/manual/
```
