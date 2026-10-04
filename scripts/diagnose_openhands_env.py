#!/usr/bin/env python3
"""
CodePro - Script de Diagnóstico e Desbloqueio Local do Ambiente OpenHands
ADR 0152: Second Executor Enablement / Preflight Environment Verification

Este script pode ser executado diretamente na sua máquina host (Windows, Linux ou macOS)
para validar e garantir que o runtime do OpenHands consiga inicializar o cache Jinja
sem requerer nenhuma gambiarra ou monkeypatch no pacote original.
"""

import sys
import os
from pathlib import Path

def diagnose_openhands_environment():
    print("=" * 65)
    print("CodePro ADR 0152 — Diagnostico de Ambiente OpenHands")
    print("=" * 65)
    
    home_dir = Path.home()
    openhands_dir = home_dir / ".openhands"
    cache_dir = openhands_dir / "cache"
    
    print(f"[*] Perfil do usuario detectado: {home_dir}")
    print(f"[*] Diretorio de destino: {openhands_dir}")
    
    try:
        # Criacao de diretorio
        cache_dir.mkdir(parents=True, exist_ok=True)
        print("[+] Criacao de pastas: OK")
        
        # Teste de escrita
        test_file = cache_dir / "adr0152_probe.tmp"
        test_payload = "CODEPRO_ADR0152_EMPIRICAL_PROBE_SUCCESS"
        test_file.write_text(test_payload, encoding="utf-8")
        print(f"[+] Escrita de arquivo de teste: OK ({test_file})")
        
        # Teste de leitura
        read_payload = test_file.read_text(encoding="utf-8")
        if read_payload == test_payload:
            print("[+] Leitura e integridade de arquivo: OK")
        else:
            print("[!] Falha de integridade na leitura!")
            return False
            
        # Limpeza
        test_file.unlink(missing_ok=True)
        print("[+] Limpeza de arquivo de teste: OK")
        
        print("\n" + "=" * 65)
        print("RESULTADO: AMBIENTE APROVADO PARA QUALIFICACAO DO OPENHANDS")
        print("Status: QUALIFIED (Sem necessidade de monkeypatch)")
        print("=" * 65)
        return True

    except PermissionError as pe:
        print("\n[!] ERRO DE PERMISSAO (EPERM / Access Denied):")
        print(f"    {pe}")
        print("\nResolucao recomendada:")
        if sys.platform == "win32":
            print(f"  Execute no PowerShell como Administrador:")
            print(f"  icacls \"{openhands_dir}\" /grant:r \"$($env:USERNAME):(OI)(CI)F\" /T")
        else:
            print(f"  Execute no terminal:")
            print(f"  mkdir -p ~/.openhands && chmod -R 755 ~/.openhands")
        return False
    except Exception as ex:
        print(f"\n[!] Falha inesperada: {ex}")
        return False

if __name__ == "__main__":
    success = diagnose_openhands_environment()
    sys.exit(0 if success else 1)
