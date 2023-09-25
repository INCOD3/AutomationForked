import requests
import time
import os

MAX_DEPTH = 0 # Define a profundidade máxima de forks a serem seguidos
RATE_LIMIT_THRESHOLD = 50  # Quantidade mínima de requisições restantes antes de interromper o script

# Códigos ANSI para cores
GREEN = "\033[92m"
RED = "\033[91m"
BLUE = "\033[94m"
ENDC = "\033[0m"  # Reset de cor

def authenticate_github(token):
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    return headers

def get_rate_limit_remaining(headers):
    url = "https://api.github.com/rate_limit"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()["rate"]["remaining"]
    else:
        print(f"Erro ao verificar o limite de taxa. Status Code: {response.status_code}")
        return 0

def fork_repository(headers, owner, repo_name):
    if get_rate_limit_remaining(headers) < RATE_LIMIT_THRESHOLD:
        print("Limite de taxa da API próximo do esgotamento. Interrompendo o processo.")
        return False
    url = f"https://api.github.com/repos/{owner}/{repo_name}/forks"
    response = requests.post(url, headers=headers)
    if response.status_code == 202:
        print(f"{GREEN}Repositório {repo_name} forked com sucesso!{ENDC}")
        return True
    elif response.status_code == 404:
        print(f"Repositório {repo_name} não encontrado. Verifique o nome do repositório.")
        return False
    elif response.status_code == 409:
        print(f"Você já deu fork em {owner}/{repo_name}.")
        return True
    else:
        print(f"Erro ao dar fork no repositório {repo_name}. Status Code: {response.status_code}")
        return False

def list_forks(headers, owner, repo_name):
    if get_rate_limit_remaining(headers) < RATE_LIMIT_THRESHOLD:
        print("Limite de taxa da API próximo do esgotamento. Interrompendo o processo.")
        return []
    url = f"https://api.github.com/repos/{owner}/{repo_name}/forks"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return [repo['full_name'] for repo in response.json()]
    else:
        print(f"Erro ao listar forks do repositório {repo_name}. Status Code: {response.status_code}")
        return []

def recursive_fork(headers, owner, repo_name, depth=0, forked_repos=None):
    if forked_repos is None:
        forked_repos = set()  # Usar um conjunto para evitar forks repetidos
    
    if depth > MAX_DEPTH:
        return
    
    repo_key = f"{owner}/{repo_name}"
    
    if repo_key in forked_repos:
        return
    
    # Dando fork no repositório especificado
    if fork_repository(headers, owner, repo_name):
        forked_repos.add(repo_key)
    
    # Esperando alguns segundos para garantir que o fork seja concluído
    time.sleep(10)
    
    # Listando os forks do repositório
    forks = list_forks(headers, owner, repo_name)
    
    # Para cada fork, chama a função de novo (recursivamente)
    for fork in forks:
        fork_owner, fork_name = fork.split('/')
        recursive_fork(headers, fork_owner, fork_name, depth + 1, forked_repos)

def get_all_repo_links(username, headers):
    url = f"https://api.github.com/users/{username}/repos?per_page=1000"  # Aumentando o limite de repositórios por página
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        repos = response.json()
        return [repo['html_url'] for repo in repos]
    else:
        print(f"Erro ao obter os repositórios do usuário {username}. Status Code: {response.status_code}")
        return []

def create_user_file(username, repo_links):
    # Cria um arquivo com o nome do usuário
    filename = "repo_links.txt"
    with open(filename, "w") as file:
        for link in repo_links:
            file.write(f"{link}\n")

def main():
    TOKEN = input("Insira seu Personal Access Token do GitHub: ")
    USERNAME = input("Insira o nome de usuário do GitHub: ")
    
    headers = authenticate_github(TOKEN)
    
    # Obtendo todos os links dos repositórios do usuário
    repo_links = get_all_repo_links(USERNAME, headers)
    
    # Verificando se o arquivo de texto existe e criando-o se não existir
    if not os.path.exists("repo_links.txt"):
        create_user_file(USERNAME, repo_links)
        print(f"Arquivo 'repo_links.txt' criado com todos os links dos repositórios do usuário {USERNAME}.")
    else:
        print(f"Arquivo 'repo_links.txt' já existe para o usuário {USERNAME}.")
    
    # Dando fork em todos os repositórios listados nos links
    for link in repo_links:
        parts = link.split("/")
        owner = parts[-2]
        repo_name = parts[-1]
        recursive_fork(headers, owner, repo_name)
    
    print(f"{BLUE}Todos os forks foram concluídos. Obrigado por usar o software!{ENDC}")

if __name__ == "__main__":
    main()
