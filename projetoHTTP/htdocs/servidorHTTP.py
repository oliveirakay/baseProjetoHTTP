#implementação de um servidor base para interpratação de métodos HTTP

import socket
import json
from bs4 import BeautifulSoup #essa biblioteca server apenas para alterar um html, nao eh nenhum tipo de framework para conexao http rest ou coisa do tipo

#definindo o endereço IP do host
SERVER_HOST = ""
#definindo o número da porta em que o servidor irá escutar pelas requisições HTTP
SERVER_PORT = 8080

#vamos criar o socket
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

#vamos setar a opção de reutilizar sockets já abertos
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

#atrela o socket ao endereço da máquina e ao número de porta definido
server_socket.bind((SERVER_HOST, SERVER_PORT))

#coloca o socket para escutar por conexões
server_socket.listen(1)

#mensagem inicial do servidor
print("Servidor em execução...")
print("Escutando por conexões na porta %s" % SERVER_PORT)
print("Acesse em: http://localhost:" + str(SERVER_PORT))
# funções auxiliares
def criaIdeia(nova_ideia):
    nomeDoArquivo = nova_ideia["titulo"] + ".html"
    with open("projetoHTTP/htdocs/"+nomeDoArquivo, 'w') as arquivo:
                    conteudo_html = """
                    <!DOCTYPE html>
                    
                    <html>
                    <head>
                    <meta charset="utf-8"/>
                    <meta content="width=device-width, initial-scale=1.0" name="viewport"/>
                        <title>""" +nova_ideia["titulo"]+"""</title>
                    </head>
                    <body>
                        <p>"""+nova_ideia["descricao"]+"""</p>
                        <p>Ideia criada por:"""+nova_ideia["emailAutor"]+"""</p>
                    </body>
                    </html>
                    """
                    arquivo.write(conteudo_html)


def mensagensDeErroHttp(status):
    if status == 409:
        msgdeErro = """HTTP/1.1 409 CONFLICT\n\n Parece que você está tentando realizar um PUT sem json ou fora do formato padrão. 
            Para realizar o PUT insira o Json no corpo da requisição como nesse exemplo:
            {"titulo":"seuTitulo","emailAutor":"seuEmail@gmail.com","descricao":"descrição da sua ideia"} \n"""
    if status == 404:
        msgdeErro = """HTTP/1.1 404 NOT FOUND\n\n<!DOCTYPE html><img alt="Banco de Ideias UFABC" src="monkey_404.jpeg"/><h1>ERROR 404!\n OPS! PARECE QUE SUA IDEIA NAO FOI ENCONTRADA :C<br>File Not Found!</h1>"""
    if status == 500:
        msgdeErro = """HTTP/1.1 500 Internal Server Error\n\n"""
    
    return msgdeErro


def adicionaIdeiaNaPaginaPrincipal(novaIdeia):
    
    # Abra o arquivo HTML e leia o conteúdo
    with open("projetoHTTP/htdocs/"+'bancoDeIdeias.html', 'r') as f:
        contents = f.read()

    soup = BeautifulSoup(contents, 'html.parser')

    # Encontre o container de ideias
    ideias_container = soup.find(id='ideias-container')

    # Crie um novo bloco de ideia
    idea_block = soup.new_tag('div')
    idea_block['class'] = 'idea-block'

    # Adicione o título, email e botão ao bloco de ideia
    titulo = soup.new_tag('h2')
    titulo.string = novaIdeia['titulo']  # Substitua pelo valor real
    idea_block.append(titulo)

    autor = soup.new_tag('p')
    autor.string = 'Autor: ' + novaIdeia['emailAutor']  # Substitua pelo valor real
    idea_block.append(autor)
    

    ancora = soup.new_tag('a', href = novaIdeia["titulo"]+".html")
    
    idea_block.append(ancora)

    botao = soup.new_tag('button', onclick='verDetalhe()')
    botao.string = 'Ver Detalhe da Ideia'
    # botaoComLink = soup.new_tag('a', href = novaIdeia["titulo"]+".html").append(botao)
    ancora.append(botao)

    # Adicione o bloco de ideia ao container de ideias
    ideias_container.append(idea_block)

    # Escreva o HTML alterado de volta ao arquivo
    with open("projetoHTTP/htdocs/"+'bancoDeIdeias.html', 'w') as f:
        f.write(str(soup))

#cria o while que irá receber as conexões
while True:

    client_connection, client_address = server_socket.accept()

    #Para receber um arquivo maior que 1024 bytes  
    request = b''
    client_connection.settimeout(0.1)
    while True:
        try:
            packet = client_connection.recv(1024)
            if not packet:
                break
            request += packet
        except socket.timeout:
            break

    # Decodifica os dados recebidos após sair do loop
    request = request.decode()
   
    #verifica se a request possui algum conteúdo (pois alguns navegadores ficam periodicamente enviando alguma string vazia)
    if request:
        #imprime a solicitação do cliente
        print(request)
        
        #analisa a solicitação HTTP
        headers = request.split("\n")
        method = request.split()[0]
        filename = headers[0].split()[1]
        # response = ''
        if filename == "/":
            filename = "/index.html"
        
        if ("put" in filename) and (method == "PUT"):

            body = request[request.find("\r\n\r\n"):]
            try:
                # pega o nome do arquivo
                filename = filename[1:]
                # escrita em modo binário para evitar erros
                newFile = open("projetoHTTP/htdocs/" + filename, "wb") 
                # cria arquivo com o body passado
                newFile.write(body.encode())
                newFile.close()
                # responde 201
                response = f"HTTP/1.1 201 Created\n\n<h1>201 CREATED!<br>File Created!</h1> <p>Acesse seu arquivo aqui <a href='http://localhost:{SERVER_PORT}/{filename}'>Novo Aquivo</a></p>"


            except Exception as e:

                # respsta para tratamento do erro
                response = mensagensDeErroHttp(500) + str(e)
                
        elif method == "PUT":
            # verifica se esta no formato json, caso n, retorna uma mensagem de erro falando que nao esta no formato json com a estrutura especificada
            try:
                # pega apenas a resposta no body do request
                data = json.loads(request.split("\r\n\r\n")[1])
                criaIdeia(data)
                adicionaIdeiaNaPaginaPrincipal(data)
                response = "HTTP/1.1 201 Created\n\n Ideia Adicionada com Sucesso"
                

            except:
                response = mensagensDeErroHttp(409)
            
        elif method == "GET":
            #try e except para tratamento de erro quando um arquivo solicitado não existir
            try:
                if filename.endswith('.jpeg') or filename.endswith('.jpg') : # se for imagem
                    fin = open("projetoHTTP/htdocs" + filename, 'rb')
                    response = fin.read()
                    response = b"HTTP/1.1 200 OK\nContent-Type: image/jpeg\n\n" + response
                    
                else:
                    #abrir o arquivo e enviar para o cliente
                    fin = open("projetoHTTP/htdocs" + filename)
                    #leio o conteúdo do arquivo para uma variável
                    content = fin.read()
                    #envia a resposta
                    response = "HTTP/1.1 200 OK\n\n" + content
                    
                #fecho o arquivo
                fin.close()
            except FileNotFoundError:
                #caso o arquivo solicitado não exista no servidor, gera uma resposta de erro
                response = mensagensDeErroHttp(404)

        # #envia a resposta HTTP
        if filename.endswith('.jpeg') or filename.endswith('.jpg') :
            client_connection.sendall(response)
        else:
            client_connection.sendall(response.encode("UTF-8"))
        
        client_connection.close()



