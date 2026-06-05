# ---------------------------------------------------------
# VideoSynk - Ferramenta Oficial HubSynk
# Versão: V.1.0
# Desenvolvido por: saulomgg (https://github.com/saulomgg)
#
# Este software faz parte do ecossistema HubSynk.
# Apoie o projeto, acesse meu portfólio e ajude a manter
# o desenvolvimento e atualizações constantes!
# ---------------------------------------------------------

import tkinter as tk
from ui.app import VideoConverterApp

def main():
    root = tk.Tk()
    app = VideoConverterApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
