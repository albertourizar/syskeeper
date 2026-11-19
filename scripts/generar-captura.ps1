<#
.SYNOPSIS
    Genera docs/captura-informe.png a partir de una ejecucion real en modo
    simulacion (no borra nada).

.DESCRIPTION
    Ejecuta "python -m syskeeper limpiar" y dibuja su salida en una ventana
    simulada de Windows Terminal con System.Drawing. No requiere dependencias
    externas: solo Windows y PowerShell 5.1.

.EXAMPLE
    powershell -NoProfile -ExecutionPolicy Bypass -File scripts\generar-captura.ps1
#>
[CmdletBinding()]
param(
    [string]$Salida = "docs\captura-informe.png",
    [string]$Usuario = "Alberto",
    [int]$Ancho = 1280,
    [float]$TamanoFuente = 14
)

$ErrorActionPreference = "Stop"
$raiz = Split-Path -Parent $PSScriptRoot
Push-Location $raiz
try {
    Add-Type -AssemblyName System.Drawing

    [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
    $env:PYTHONIOENCODING = "utf-8"

    Write-Host "Capturando salida real de syskeeper..."
    $lineas = & python -m syskeeper limpiar --sin-informe --sin-espacio --sin-color 2>&1 |
        ForEach-Object { $_.ToString() }

    $prompt = "PS C:\Users\$Usuario\syskeeper> python -m syskeeper limpiar"
    $texto = @($prompt, "") + @($lineas)

    $fuente = New-Object System.Drawing.Font("Consolas", $TamanoFuente)
    $tituloFuente = New-Object System.Drawing.Font("Segoe UI", 11)
    $altoLinea = [int]($fuente.GetHeight() + 4)
    $margen = 26
    $altoBarra = 38
    $alto = $altoBarra + 24 + ($texto.Count * $altoLinea) + 24

    $bitmap = New-Object System.Drawing.Bitmap([int]$Ancho, [int]$alto)
    $grafico = [System.Drawing.Graphics]::FromImage($bitmap)
    $grafico.TextRenderingHint = [System.Drawing.Text.TextRenderingHint]::ClearTypeGridFit

    $fondo = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(13, 17, 23))
    $barra = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(30, 35, 44))
    $tituloColor = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(201, 209, 217))
    $blanco = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(229, 236, 243))
    $azul = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(121, 192, 255))
    $verde = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(63, 185, 80))
    $ambar = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(210, 153, 34))
    $gris = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(139, 148, 158))
    $circuloRojo = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(255, 95, 86))
    $circuloAmarillo = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(255, 189, 46))
    $circuloVerde = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(39, 201, 63))

    $grafico.FillRectangle($fondo, 0, 0, $Ancho, $alto)
    $grafico.FillRectangle($barra, 0, 0, $Ancho, $altoBarra)
    $grafico.FillEllipse($circuloRojo, 16, 13, 12, 12)
    $grafico.FillEllipse($circuloAmarillo, 36, 13, 12, 12)
    $grafico.FillEllipse($circuloVerde, 56, 13, 12, 12)
    $grafico.DrawString("syskeeper - PowerShell", $tituloFuente, $tituloColor, 84, 9)

    $y = $altoBarra + 18
    foreach ($linea in $texto) {
        if ([string]::IsNullOrWhiteSpace($linea)) {
            $y += $altoLinea
            continue
        }
        $color = $blanco
        if ($linea -match '^(=+|syskeeper v| Modo:|->)' -or $linea.Contains([char]0x2192)) {
            $color = $azul
        }
        elseif ($linea -match '^Resultado:.*correcto') {
            $color = $verde
        }
        elseif ($linea -match '^Resultado:') {
            $color = $ambar
        }
        elseif ($linea -match '^(Nota:|-{4,}|  )') {
            $color = $gris
        }
        $grafico.DrawString($linea, $fuente, $color, $margen, $y)
        $y += $altoLinea
    }

    $carpeta = Split-Path -Parent $Salida
    if ($carpeta -and -not (Test-Path $carpeta)) {
        New-Item -ItemType Directory -Path $carpeta -Force | Out-Null
    }
    $bitmap.Save((Join-Path $raiz $Salida), [System.Drawing.Imaging.ImageFormat]::Png)

    $grafico.Dispose()
    $bitmap.Dispose()
    $fuente.Dispose()
    $tituloFuente.Dispose()

    Write-Host "Captura guardada en: $(Join-Path $raiz $Salida)"
}
finally {
    Pop-Location
}
