# paper_review_llm
## Deployment
All run in a same node
```
                                                   .---> Ollama 1
User --> Traefik:80 --> Streamlit --> traefik lb --|
                                                   '---> Ollama 2
```

- Deploy traefik
    ```
    docker compose -f traefik-docker.yaml up
    ```
- Run streamlit
    ```
    pip install -r requirements.txt
    streamlit run main.py --server.address=localhost
    ```
- Run ollama
    ```
    docker run -d --gpus=0 --network=host -v /storage1/tu/olla:/root/.ollama -e OLLAMA_KEEP_ALIVE=500m -e OLLAMA_HOST=localhost:11440 --name tu_ollama_0 ollama/ollama

    docker run -d --gpus=1 --network=host -v /storage1/tu/olla:/root/.ollama -e OLLAMA_KEEP_ALIVE=500m -e OLLAMA_HOST=localhost:11441 --name tu_ollama_1 ollama/ollama
    ```
- Go to ollama docker and download/import model. They share same volume so only need to do once.
    ```
    docker exec -ih tu_ollama_0 bash
    ```
