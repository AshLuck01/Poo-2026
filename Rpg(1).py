import random
import sys
import os
import pygame

pygame.init()
pygame.font.init()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def cam(nome_arquivo):
    return os.path.join(BASE_DIR, nome_arquivo)

LARGURA, ALTURA = 1024, 768
tela = pygame.display.set_mode((LARGURA, ALTURA))
pygame.display.set_caption("Text Knight")
relogio = pygame.time.Clock()

img_fundo = pygame.image.load(cam("Background.png")).convert()
img_fundo = pygame.transform.scale(img_fundo, (LARGURA, ALTURA))

img_btn_atk = pygame.image.load(cam("Ataque.png")).convert_alpha()
img_btn_atk = pygame.transform.scale(img_btn_atk, (160, 45))

img_btn_def = pygame.image.load(cam("Defesa.png")).convert_alpha()
img_btn_def = pygame.transform.scale(img_btn_def, (160, 45))

img_btn_heal = pygame.image.load(cam("Cura.png")).convert_alpha()
img_btn_heal = pygame.transform.scale(img_btn_heal, (160, 45))

img_barra_vida_player = pygame.image.load(cam("Vida_P.png")).convert_alpha()


def carregar_guerreiro():
    return {
        "idle": pygame.transform.scale(pygame.image.load(cam("guerreiro-ataque-1.png")).convert_alpha(), (130, 160)), 
        "ataque": pygame.transform.scale(pygame.image.load(cam("guerreiro-ataque-2.png")).convert_alpha(), (130, 160)),
        "dano": pygame.transform.scale(pygame.image.load(cam("Guerreiro-dano.png")).convert_alpha(), (130, 160)),
        "morto": pygame.transform.scale(pygame.image.load(cam("guerreiro-morto.png")).convert_alpha(), (130, 160))
    }

def carregar_arqueiro():
    return {
        "idle": pygame.transform.scale(pygame.image.load(cam("Arqueiro-idle.png")).convert_alpha(), (130, 160)),
        "ataque": pygame.transform.scale(pygame.image.load(cam("Arqueiro-ataque.png")).convert_alpha(), (130, 160)),
        "dano": pygame.transform.scale(pygame.image.load(cam("Arqueiro-dano.png")).convert_alpha(), (130, 160)),
        "morto": pygame.transform.scale(pygame.image.load(cam("Arqueiro-morto.png")).convert_alpha(), (130, 160))
    }

def carregar_feiticeira():
    return {
        "idle": pygame.transform.scale(pygame.image.load(cam("Feiticeira-idle.png")).convert_alpha(), (130, 160)),
        "ataque": pygame.transform.scale(pygame.image.load(cam("feiticeira-ataque-2.png")).convert_alpha(), (130, 160)), 
        "dano": pygame.transform.scale(pygame.image.load(cam("Feiticeira-dano.png")).convert_alpha(), (130, 160)),
        "morto": pygame.transform.scale(pygame.image.load(cam("feiticeira-morta.png")).convert_alpha(), (130, 160))
    }


COR_BG = (10, 10, 12)
COR_TEXTO = (255, 255, 255)
COR_CAIXA_PRETA = (0, 0, 0)
COR_BOTAO_HOVER = (100, 149, 237)
COR_BOTAO_ALVO = (147, 112, 219) 
COR_BOTAO_RESET = (178, 34, 34)

NEON_COMBATENTE = (50, 205, 50)   
NEON_ARQUEIRO = (255, 140, 0)    
NEON_MAGO = (138, 43, 226)      

fonte_principal = pygame.font.SysFont("Arial", 18)
fonte_titulo = pygame.font.SysFont("Arial", 26, bold=True)
fonte_vida = pygame.font.SysFont("Arial", 16, bold=True)


class Entidade:
    def __init__(self, nome, classe, hp_max, resistencia, esquiva, cor_neon):
        self.nome = nome
        self.classe = classe
        self.hp_max = hp_max
        self.hp = hp_max
        self.resistencia = resistencia  
        self.esquiva = esquiva          
        self.cor_neon = cor_neon
        self.bloqueando = False
        self.x = 0
        self.y = 0
        self.modificadores = {"critico": 1.0, "defesa_extra": 0}
        
        self.sprites = {}
        self.estado_atual = "idle"
        self.timer_estado = 0

    def esta_vivo(self):
        return self.hp > 0

    def atualizar_estado(self):
        if self.timer_estado > 0:
            self.timer_estado -= 1
            if self.timer_estado == 0:
                if self.esta_vivo():
                    self.estado_atual = "idle"

    def definir_estado(self, estado, duracao):
        if self.esta_vivo() or estado == "morto":
            self.estado_atual = estado
            self.timer_estado = duracao

    def desenhar(self, superficie):
        sprite_para_desenhar = self.sprites.get(self.estado_atual, self.sprites.get("idle"))
        if sprite_para_desenhar:
            rect = sprite_para_desenhar.get_rect(center=(self.x, self.y))
            superficie.blit(sprite_para_desenhar, rect.topleft)


class Jogador(Entidade):
    def __init__(self, nome, classe, hp_max, resistencia, esquiva, cor_neon):
        super().__init__(nome, classe, hp_max, resistencia, esquiva, cor_neon)
        self.potacoes_restantes = 3
        self.x = 512
        self.y = 580
        self.sprites = carregar_guerreiro()

    def tomar_dano(self, dano_bruto):
        defesa_total = self.resistencia + self.modificadores["defesa_extra"]

        if self.bloqueando:
            defesa_total *= 2

        dano_final = max(1, int(dano_bruto - defesa_total))
        self.hp = max(0, self.hp - dano_final)

        if self.hp <= 0:
            self.definir_estado("morto", 0)
        else:
            self.definir_estado("dano", 12)

        return dano_final


class Inimigo(Entidade):
    def __init__(self, nome, classe, hp_max, resistencia, esquiva, cor_neon, pos_x):
        super().__init__(nome, classe, hp_max, resistencia, esquiva, cor_neon)
        self.x = pos_x
        self.y = 400 
        self.dano_ataque = 12
        self.configurar_classe()

    def configurar_classe(self):
        if self.classe == "Mago":
            self.dano_ataque = 22      
            self.sprites = carregar_feiticeira()
        elif self.classe == "Arqueiro":
            self.dano_ataque = 14
            self.sprites = carregar_arqueiro()
        else:
            self.dano_ataque = 10
            self.sprites = carregar_guerreiro() 

    def calcular_dano_recebido(self, valor_ataque, d20):
        if self.classe == "Arqueiro" and random.randint(1, 100) <= self.esquiva and d20 != 20:
            return False, 0
        
        dano_final = max(1, valor_ataque - self.resistencia)
        self.hp = max(0, self.hp - dano_final)
        
        if self.hp <= 0:
            self.definir_estado("morto", 0)
        else:
            self.definir_estado("dano", 15)
            
        return True, dano_final


class Jogo:
    def __init__(self):
        self.recorde_ondas = 0  
        self.log_mensagens = [] 
        self.timer_animacao = 0
        self.tipo_animacao = None
        self.alvo_animacao_x = 0
        self.timer_transicao_onda = 0
        self.resetar_jogo()

    def adicionar_log(self, texto):
        self.log_mensagens.append(texto)
        if len(self.log_mensagens) > 4:
            self.log_mensagens.pop(0)

    def resetar_jogo(self):
        self.jogador = Jogador("Você (Guerreiro)", "Guerreiro", hp_max=200, resistencia=8, esquiva=5, cor_neon=COR_TEXTO)
        self.onda_atual = 1
        self.ondas_vencidas = 0
        self.inimigos = []
        self.log_mensagens = []
        self.adicionar_log("--- Nova Jornada Iniciada ---")
        self.adicionar_log("Inimigos à vista bem na sua frente! Segure firme sua arma.")
        self.gerar_onda()
        self.escolhendo_alvo = False 
        self.timer_transicao_onda = 0

    def rolar_d20(self):
        return random.randint(1, 20)

    def gerar_onda(self):
        self.inimigos = []
        qtd_inimigos = random.randint(1, 3)
        
        if qtd_inimigos == 1:
            posicoes_x = [512]
        elif qtd_inimigos == 2:
            posicoes_x = [362, 662]
        else:
            posicoes_x = [212, 512, 812]

        pool_classes = [
            {"classe": "Combatente", "hp": 90, "res": 14, "esq": 5, "cor": NEON_COMBATENTE},
            {"classe": "Arqueiro", "hp": 65, "res": 4, "esq": 40, "cor": NEON_ARQUEIRO},
            {"classe": "Mago", "hp": 35, "res": 0, "esq": 10, "cor": NEON_MAGO}
        ]
         
        for i in range(qtd_inimigos):
            dados_classe = random.choice(pool_classes)
            px = posicoes_x[i]
            
            ini = Inimigo(
                nome=f"{dados_classe['classe']} {i+1}",
                classe=dados_classe['classe'],
                hp_max=dados_classe['hp'],
                resistencia=dados_classe['res'],
                esquiva=dados_classe['esq'],
                cor_neon=dados_classe['cor'],
                pos_x=px
            )
            self.inimigos.append(ini)

    def processar_turno_inimigos(self):
        if not self.jogador.esta_vivo():
            return

        for ini in self.inimigos:
            if ini.esta_vivo():
                ini.definir_estado("ataque", 18) 
                dano_causado = self.jogador.tomar_dano(ini.dano_ataque)
                self.adicionar_log(f" {ini.nome} avançou em você e causou {dano_causado} de dano!")
        
        self.adicionar_log("Sua vez! Escolha seu próximo movimento.")
        self.jogador.bloqueando = False 

    def realizar_ataque(self, indice_alvo):
        alvo = self.inimigos[indice_alvo]
        d20 = self.rolar_d20()
        
        self.jogador.definir_estado("ataque", 18)
        self.tipo_animacao = "ESPADA"
        self.alvo_animacao_x = alvo.x
        self.timer_animacao = 18
        
        if d20 == 1:
            self.adicionar_log(f" D20: 1 (Falha Crítica)! Você errou o golpe completamente contra o {alvo.nome}!")
        else:
            dano = random.randint(25, 35)
            if d20 == 20: 
                dano = int(dano * 2 * self.jogador.modificadores["critico"])
                _, dano_causado = alvo.calcular_dano_recebido(dano, d20)
                self.adicionar_log(f" D20: 20! GOLPE CRÍTICO EM CHEIO! {alvo.nome} sofreu {dano_causado} de dano!")
            else: 
                dano += d20
                sucesso, dano_causado = alvo.calcular_dano_recebido(dano, d20)
                if sucesso:
                    self.adicionar_log(f" D20: {d20}. Você golpeou {alvo.nome} causando {dano_causado} de dano.")
                else:
                    self.adicionar_log(f" {alvo.nome} foi mais rápido e esquivou do seu ataque frontal!")

        self.escolhendo_alvo = False

    def acionar_bloqueio(self):
        self.jogador.bloqueando = True
        self.tipo_animacao = "ESCUDO"
        self.timer_animacao = 18
        self.adicionar_log(" Você levantou a guarda! Próximos ataques diretos causarão menos dano.")

    def usar_pocao(self):
        if self.jogador.potacoes_restantes > 0:
            self.jogador.hp = min(self.jogador.hp_max, self.jogador.hp + 75)
            self.jogador.potacoes_restantes -= 1
            self.tipo_animacao = "POCAO"
            self.timer_animacao = 18
            self.adicionar_log(" Você tomou a poção e recuperou 75 de vida!")
        else:
            self.adicionar_log(" Suas poções de cura acabaram!")

    def atualizar_entidades(self):
        self.jogador.atualizar_estado()
        for ini in self.inimigos:
            ini.atualizar_estado()


def finalizar_rodada(jogo):
    if any(ini.esta_vivo() for ini in jogo.inimigos):
        jogo.processar_turno_inimigos()
        return
        
    if jogo.timer_transicao_onda == 0:
        jogo.timer_transicao_onda = 30


def desenhar_interface(jogo):
    tela.blit(img_fundo, (0, 0))

    jogo.atualizar_entidades()

    pygame.draw.rect(tela, COR_CAIXA_PRETA, (80, 30, 864, 115))
    pygame.draw.rect(tela, (50, 50, 60), (80, 30, 864, 115), 2)
    
    for idx, msg in enumerate(jogo.log_mensagens):
        cor_linha = (160, 160, 160) if idx < len(jogo.log_mensagens) - 1 else COR_TEXTO
        txt_renderizado = fonte_principal.render(msg, True, cor_linha)
        tela.blit(txt_renderizado, (100, 38 + (idx * 24)))

    for ini in jogo.inimigos:
        ini.desenhar(tela)
        if ini.esta_vivo():
            pygame.draw.rect(tela, (100, 0, 0), (ini.x - 60, ini.y - 110, 120, 8))
            largura_barra = int((ini.hp / ini.hp_max) * 120)
            pygame.draw.rect(tela, ini.cor_neon, (ini.x - 60, ini.y - 110, largura_barra, 8))
            
            txt_nome_ini = fonte_vida.render(f"{ini.nome} [{ini.hp}/{ini.hp_max}]", True, COR_TEXTO)
            tela.blit(txt_nome_ini, txt_nome_ini.get_rect(center=(ini.x, ini.y - 90)))

    if jogo.jogador.estado_atual == "ataque" and jogo.timer_animacao > 0:
        sprite_atk = jogo.jogador.sprites.get("ataque")
        if sprite_atk:
            rect_atk = sprite_atk.get_rect(center=(jogo.alvo_animacao_x, 480))
            tela.blit(sprite_atk, rect_atk.topleft)

    if jogo.timer_animacao > 0:
        jogo.timer_animacao -= 1
        if jogo.tipo_animacao == "ESPADA":
            ex = jogo.alvo_animacao_x
            pygame.draw.line(tela, (255, 255, 255), (ex - 70, 340), (ex + 70, 460), 8)
            pygame.draw.line(tela, (240, 240, 250), (ex - 60, 335), (ex + 60, 455), 3)
        elif jogo.tipo_animacao == "ESCUDO":
            pygame.draw.polygon(tela, (30, 144, 255), [(412, 380), (612, 380), (582, 550), (512, 600), (442, 550)])
            pygame.draw.polygon(tela, COR_TEXTO, [(412, 380), (612, 380), (582, 550), (512, 600), (442, 550)], 3)
        elif jogo.tipo_animacao == "POCAO":
            pygame.draw.circle(tela, (0, 255, 0), (512, 384), 40, 3)

        if jogo.timer_animacao == 0:
            finalizar_rodada(jogo)

    if jogo.timer_transicao_onda > 0:
        jogo.timer_transicao_onda -= 1
        if jogo.timer_transicao_onda == 0:
            jogo.ondas_vencidas += 1
            if jogo.ondas_vencidas > jogo.recorde_ondas:
                jogo.recorde_ondas = jogo.ondas_vencidas
            jogo.onda_atual += 1
            jogo.adicionar_log(f" Vitória! Área limpa. Nova horda se aproximando (Onda {jogo.onda_atual})!")
            
            if jogo.ondas_vencidas % 5 == 0:
                jogo.jogador.potacoes_restantes += 1
                jogo.adicionar_log(f" BÔNUS! Você limpou 5 salas e achou +1 Poção!")
                
            jogo.gerar_onda()

    pygame.draw.rect(tela, COR_CAIXA_PRETA, (80, 630, 864, 90))
    pygame.draw.rect(tela, (192, 192, 192), (80, 630, 864, 90), 2)

    mouse_pos = pygame.mouse.get_pos()
    clicou = pygame.mouse.get_pressed()[0]
    acao_selecionada = None

    if jogo.jogador.esta_vivo():
        largura_maxima_vida = 250
        largura_sua_vida = int((jogo.jogador.hp / jogo.jogador.hp_max) * largura_maxima_vida)
        
        txt_seu_hp_num = fonte_vida.render(f"SUA VIDA   HP: {jogo.jogador.hp} / {jogo.jogador.hp_max}", True, COR_TEXTO)
        tela.blit(txt_seu_hp_num, (100, 640))
        
        pygame.draw.rect(tela, (150, 0, 0), (420, 642, largura_maxima_vida, 12))
        pygame.draw.rect(tela, (0, 220, 50), (420, 642, largura_sua_vida, 12))

        img_borda_redimensionada = pygame.transform.scale(img_barra_vida_player, (largura_sua_vida + 20, 30))
        tela.blit(img_borda_redimensionada, (410, 633))

        txt_pot = fonte_vida.render(f"Poções: {jogo.jogador.potacoes_restantes}", True, (218, 165, 32))
        tela.blit(txt_pot, (710, 640))
        txt_vits = fonte_vida.render(f"Ondas Vencidas: {jogo.ondas_vencidas}", True, COR_TEXTO)
        tela.blit(txt_vits, (810, 640))

        if jogo.timer_animacao == 0 and jogo.timer_transicao_onda == 0:
            if not jogo.escolhendo_alvo:
                botoes = [
                    ("MENU_ALVO", (100, 665, 160, 45), img_btn_atk), 
                    ("ACT_BLOQUEAR", (280, 665, 160, 45), img_btn_def), 
                    ("POTION", (460, 665, 160, 45), img_btn_heal)
                ]
                for acao, ret, img_renderizar in botoes:
                    rect_obj = pygame.Rect(ret)
                    tela.blit(img_renderizar, rect_obj.topleft)
                    
                    if rect_obj.collidepoint(mouse_pos):
                        pygame.draw.rect(tela, COR_BOTAO_HOVER, rect_obj, 2)
                        if clicou: acao_selecionada = acao
                    else:
                        pygame.draw.rect(tela, COR_CAIXA_PRETA, rect_obj, 1)
            else:
                pos_btn_x = 100
                for i, ini in enumerate(jogo.inimigos):
                    if ini.esta_vivo():
                        rect_alvo = pygame.Rect((pos_btn_x, 665, 140, 45))
                        if rect_alvo.collidepoint(mouse_pos):
                            pygame.draw.rect(tela, COR_TEXTO, rect_alvo)
                            texto_cor = (0, 0, 0)
                            if clicou: acao_selecionada = f"ALVO_{i}"
                        else:
                            pygame.draw.rect(tela, COR_BOTAO_ALVO, rect_alvo)
                            texto_cor = COR_TEXTO
                            
                        pygame.draw.rect(tela, COR_TEXTO, rect_alvo, 1)
                        txt_btn_alvo = fonte_vida.render(ini.nome, True, texto_cor)
                        tela.blit(txt_btn_alvo, txt_btn_alvo.get_rect(center=rect_alvo.center))
                        pos_btn_x += 160
                
                rect_voltar = pygame.Rect((780, 665, 100, 45))
                if rect_voltar.collidepoint(mouse_pos):
                    pygame.draw.rect(tela, (200, 20, 20), rect_voltar)
                    if clicou: acao_selecionada = "VOLTAR"
                else:
                    pygame.draw.rect(tela, COR_BOTAO_RESET, rect_voltar)
                pygame.draw.rect(tela, COR_TEXTO, rect_voltar, 1)
                txt_voltar = fonte_vida.render("Voltar", True, COR_TEXTO)
                tela.blit(txt_voltar, txt_voltar.get_rect(center=rect_voltar.center))
    else:
        rect_reset = pygame.Rect((412, 655, 200, 45))
        if rect_reset.collidepoint(mouse_pos):
            pygame.draw.rect(tela, (220, 20, 60), rect_reset)
            if clicou: acao_selecionada = "RESET"
        else:
            pygame.draw.rect(tela, COR_BOTAO_RESET, rect_reset)
        pygame.draw.rect(tela, COR_TEXTO, rect_reset, 1)
        txt_reset = fonte_vida.render("Renascer", True, COR_TEXTO)
        tela.blit(txt_reset, txt_reset.get_rect(center=rect_reset.center))

    pygame.display.flip()
    return acao_selecionada


def main():
    jogo = Jogo()
    executando = True
    travar_clique = False

    while executando:
        relogio.tick(30)
        
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                executando = False

        acao = desenhar_interface(jogo)

        if acao and not travar_clique:
            if acao == "RESET":
                jogo.resetar_jogo()
            elif acao == "MENU_ALVO":
                jogo.escolhendo_alvo = True
            elif acao == "VOLTAR":
                jogo.escolhendo_alvo = False
            elif acao == "ACT_BLOQUEAR":
                jogo.acionar_bloqueio()
            elif acao == "POTION":
                jogo.usar_pocao()
            elif acao.startswith("ALVO_"):
                indice = int(acao.split("_")[1])
                jogo.realizar_ataque(indice)
                
            travar_clique = True 

        if not pygame.mouse.get_pressed()[0]:
            travar_clique = False

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()