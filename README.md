## Installing ollama 

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

download mistral model

```bash
ollama pull mistral
```

creating customized model with Modelfile
```bash
ollama create mental-mistral -f Modelfile
```

now run the model 

```bash
ollama run mental-mistral:latest --keepalive=-1m
```

`--keepalive=-1m` will stop model unloading from memory.
so now model is always in the memory even if their are no requests for long time.
