## Logging

A aplicação sempre escreve logs estruturados no console. Para persistir os logs
em MongoDB (incluindo Amazon DocumentDB ou MongoDB Atlas hospedado na AWS),
configure:

```bash
export MONGODB_URI='mongodb://usuario:senha@host:27017/?tls=true&replicaSet=rs0&readPreference=secondaryPreferred&retryWrites=false'
export MONGODB_DATABASE='pilot_study'
export MONGODB_LOG_COLLECTION='application_logs'
export MONGODB_TLS_CA_FILE='/caminho/global-bundle.pem' # Amazon DocumentDB
export LOG_LEVEL='INFO'
```

`MONGODB_URI` deve ser fornecida por um secret do ambiente de execução; não a
adicione ao código ou ao repositório. A coleção é criada automaticamente no
primeiro log. Para Amazon DocumentDB, forneça também o certificado CA no URI
ou configure o certificado no ambiente conforme a documentação do serviço.