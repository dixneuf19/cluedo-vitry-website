# Déploiement Kubernetes - Blog Sam Marsalis

Ce dossier contient les manifests Kubernetes pour déployer le blog de Sam Marsalis sur un cluster Kubernetes.

## Prérequis

- Cluster Kubernetes fonctionnel
- `kubectl` configuré
- Ingress Controller (nginx recommandé)
- Cert-Manager pour les certificats HTTPS (optionnel)

## Configuration

### 1. Modifier le domaine

Editez `ingress.yaml` et remplacez `cluedo-vitry.your-domain.com` par votre domaine réel.

### 2. Modifier le mot de passe admin

Pour changer le mot de passe admin par défaut (`admin123`) :

```bash
# Encoder votre nouveau mot de passe
echo -n "votre-nouveau-mot-de-passe" | base64

# Modifier secret.yaml avec la valeur encodée
```

### 3. Adapter l'image Docker

Si vous utilisez un registry différent, modifiez `kustomization.yaml` :

```yaml
images:
- name: ghcr.io/votre-username/cluedo-vitry
  newTag: latest
```

## Déploiement

### Méthode 1: Avec Kustomize (recommandé)

```bash
# Déployer tout d'un coup
kubectl apply -k k8s/

# Ou avec kustomize directement
kustomize build k8s/ | kubectl apply -f -
```

### Méthode 2: Fichier par fichier

```bash
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secret.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/ingress.yaml
```

## Vérification

```bash
# Vérifier les pods
kubectl get pods -n cluedo-vitry

# Vérifier le service
kubectl get svc -n cluedo-vitry

# Vérifier l'ingress
kubectl get ingress -n cluedo-vitry

# Voir les logs
kubectl logs -n cluedo-vitry -l app.kubernetes.io/name=cluedo-vitry
```

## Accès

- **Blog public** : `https://cluedo-vitry.your-domain.com`
- **Admin panel** : `https://cluedo-vitry.your-domain.com/admin/`

## Mise à jour

Pour mettre à jour l'application avec une nouvelle image :

```bash
# Modifier le tag dans kustomization.yaml puis
kubectl apply -k k8s/

# Ou directement avec kubectl
kubectl set image deployment/cluedo-vitry blog=ghcr.io/padoa/cluedo-vitry:new-tag -n cluedo-vitry
```

## Suppression

```bash
# Supprimer tout
kubectl delete -k k8s/

# Ou supprimer juste l'application (garder le namespace)
kubectl delete -f k8s/deployment.yaml
kubectl delete -f k8s/service.yaml
kubectl delete -f k8s/ingress.yaml
```

## Structure des ressources

- **Namespace** : `cluedo-vitry` - Isolation des ressources
- **ConfigMap** : Configuration non-sensible (port, etc.)
- **Secret** : Mot de passe admin (encodé base64)
- **Deployment** : 2 réplicas avec health checks
- **Service** : Exposition interne port 80
- **Ingress** : Exposition externe avec HTTPS

## Sécurité

L'application est configurée avec :
- Utilisateur non-root (UID 1000)
- Ressources limitées (128Mi RAM, 200m CPU)
- Health checks (liveness + readiness)
- HTTPS forcé via Ingress
- Capacités de sécurité restreintes 
