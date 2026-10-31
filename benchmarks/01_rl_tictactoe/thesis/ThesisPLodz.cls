%% ThesisPLodz.cls
%% Szablon Pracy Dyplomowej Politechniki Łódzkiej
%% Zgodny z Zarządzeniem Nr 6/2025 Rektora Politechniki Łódzkiej z dnia 11 marca 2025 r.
%% Opracowanie na podstawie wzorca dr. inż. Piotra Łuczaka (Instytut Informatyki Stosowanej PŁ)

\NeedsTeXFormat{LaTeX2e}
\ProvidesClass{ThesisPLodz}[2025/03/11 v1.0 Szablon Pracy Dyplomowej Politechniki Lodzkiej]

% --- Opcje klasy ---
\RequirePackage{kvoptions}
\SetupKeyvalOptions{family=ThesisPLodz, prefix=TPL@}

% Wydziały Politechniki Łódzkiej
\newcommand{\TPL@faculty}{Wydzia{\l} Elektrotechniki, Elektroniki, Informatyki i Automatyki}
\DeclareVoidOption{W1}{\renewcommand{\TPL@faculty}{Wydzia{\l} Mechaniczny}}
\DeclareVoidOption{W2}{\renewcommand{\TPL@faculty}{Wydzia{\l} Elektrotechniki, Elektroniki, Informatyki i Automatyki}}
\DeclareVoidOption{W3}{\renewcommand{\TPL@faculty}{Wydzia{\l} Chemiczny}}
\DeclareVoidOption{W4}{\renewcommand{\TPL@faculty}{Wydzia{\l} Technologii Materia{\l}owych i Wzornictwa Tekstyli{\'o}w}}
\DeclareVoidOption{W5}{\renewcommand{\TPL@faculty}{Wydzia{\l} Biotechnologii i Nauk o {\.Z}ywno{\'s}ci}}
\DeclareVoidOption{W6}{\renewcommand{\TPL@faculty}{Wydzia{\l} Budownictwa, Architektury i In{\.z}ynierii {\'S}rodowiska}}
\DeclareVoidOption{W7}{\renewcommand{\TPL@faculty}{Wydzia{\l} Fizyki Technicznej, Informatyki i Matematyki Stosowanej}}
\DeclareVoidOption{W8}{\renewcommand{\TPL@faculty}{Wydzia{\l} Organizacji i Zarz{\k{a}}dzania}}
\DeclareVoidOption{W9}{\renewcommand{\TPL@faculty}{Wydzia{\l} In{\.z}ynierii Procesowej i Ochrony {\'S}rodowiska}}
\DeclareVoidOption{IFE}{\renewcommand{\TPL@faculty}{Centrum Kszta{\l}cenia Mi{\k{e}}dzynarodowego / International Faculty of Engineering}}

% Języki
\newif\ifTPL@polish
\newif\ifTPL@english
\newif\ifTPL@french
\TPL@polishtrue
\DeclareVoidOption{polski}{\TPL@polishtrue\TPL@englishfalse\TPL@frenchfalse}
\DeclareVoidOption{english}{\TPL@polishfalse\TPL@englishtrue\TPL@frenchfalse}
\DeclareVoidOption{francaise}{\TPL@polishfalse\TPL@englishfalse\TPL@frenchtrue}

% Poufność
\newif\ifTPL@confidential
\TPL@confidentialfalse
\DeclareVoidOption{confidential}{\TPL@confidentialtrue}

\DeclareDefaultOption{\PassOptionsToClass{\CurrentOption}{report}}
\ProcessKeyvalOptions*
\ProcessOptions\relax

\LoadClass[11pt,a4paper,twoside,openright]{report}

% --- Pakiety bazowe ---
\RequirePackage{iftex}
\ifxetex
  \RequirePackage{fontspec}
\else\ifluatex
  \RequirePackage{fontspec}
\else
  \RequirePackage[utf8]{inputenc}
  \RequirePackage[T1]{fontenc}
  \RequirePackage{lmodern}
\fi\fi
\RequirePackage[a4paper,inner=3.0cm,outer=2.5cm,top=2.5cm,bottom=2.5cm,headsep=0.7cm,footskip=1.0cm]{geometry}
\RequirePackage{graphicx}
\RequirePackage{amsmath,amssymb,bm}
\RequirePackage{booktabs}
\RequirePackage{fancyhdr}
\RequirePackage{listings}
\RequirePackage{xcolor}
\RequirePackage{setspace}
\RequirePackage{tikz}
\RequirePackage[hidelinks]{hyperref}

\ifTPL@polish
  \RequirePackage[polish]{babel}
\else\ifTPL@english
  \RequirePackage[english]{babel}
\else
  \RequirePackage[french]{babel}
\fi\fi

\onehalfspacing

% --- Definicje pól metadanych ---
\newcommand{\authortitle}[1]{\def\TPL@authortitle{#1}}
\newcommand{\authorname}[1]{\def\TPL@authorname{#1}}
\newcommand{\studentnumber}[1]{\def\TPL@studentnumber{#1}}
\newcommand{\boldauthorinbib}[1]{\def\TPL@boldauthorinbib{#1}}
\newcommand{\thesistitle}[1]{\def\TPL@thesistitle{#1}}
\newcommand{\thesisshorttitle}[1]{\def\TPL@thesisshorttitle{#1}}
\newcommand{\degreename}[1]{\def\TPL@degreename{#1}}
\newcommand{\fieldofstudy}[1]{\def\TPL@fieldofstudy{#1}}
\newcommand{\department}[1]{\def\TPL@department{#1}}
\newcommand{\supervisor}[1]{\def\TPL@supervisor{#1}}
\newcommand{\cosupervisor}[1]{\def\TPL@cosupervisor{#1}}
\newcommand{\partnersupervisor}[1]{\def\TPL@partnersupervisor{#1}}
\newcommand{\bibliographyfile}[1]{\def\TPL@bibliographyfile{#1}}
\renewcommand{\abstract}[1]{\def\TPL@abstract{#1}}
\newcommand{\keywords}[1]{\def\TPL@keywords{#1}}
\newcommand{\abstractsecondary}[1]{\def\TPL@abstractsecondary{#1}}
\newcommand{\keywordssecondary}[1]{\def\TPL@keywordssecondary{#1}}
\newcommand{\copynumber}[1]{\def\TPL@copynumber{#1}}

% Domyślne wartości
\def\TPL@authortitle{}
\def\TPL@authorname{Imi\k{e} i Nazwisko Autora}
\def\TPL@studentnumber{000000}
\def\TPL@thesistitle{Tytu{\l} Pracy Dyplomowej}
\def\TPL@thesisshorttitle{Kr{\'o}tki tytu{\l} pracy}
\def\TPL@degreename{in{\.z}ynierska}
\def\TPL@fieldofstudy{Sztuczna Inteligencja i Uczenie Maszynowe}
\def\TPL@department{Instytut Informatyki Stosowanej}
\def\TPL@supervisor{Promotor Pracy}
\def\TPL@cosupervisor{}
\def\TPL@partnersupervisor{}
\def\TPL@bibliographyfile{references}
\def\TPL@abstract{}
\def\TPL@keywords{}
\def\TPL@abstractsecondary{}
\def\TPL@keywordssecondary{}
\def\TPL@copynumber{1}

% Listy specjalne (opcjonalne)
\newcommand{\symbolslist}[1]{\def\TPL@symbolslist{#1}}
\newcommand{\abbreviationslist}[1]{\def\TPL@abbreviationslist{#1}}
\newcommand{\definitionslist}[1]{\def\TPL@definitionslist{#1}}
\def\TPL@symbolslist{}
\def\TPL@abbreviationslist{}
\def\TPL@definitionslist{}

% Załączniki
\newcommand{\addattachment}[2]{%
  \chapter*{Za{\l}{\k{a}}cznik: #1}%
  \addcontentsline{toc}{chapter}{Za{\l}{\k{a}}cznik: #1}%
  #2\par%
}
\newcommand{\addpdfattachment}[2]{%
  \chapter*{Za{\l}{\k{a}}cznik (PDF): #1}%
  \addcontentsline{toc}{chapter}{Za{\l}{\k{a}}cznik (PDF): #1}%
  \textit{Plik za{\l}{\k{a}}cznika: \texttt{#2}}\par%
}

% --- Nagłówki i stopki ---
\pagestyle{fancy}
\fancyhf{}
\fancyhead[LE]{\small \TPL@authortitle\ \TPL@authorname}
\fancyhead[RO]{\small \TPL@thesisshorttitle}
\fancyfoot[C]{\thepage}
\renewcommand{\headrulewidth}{0.4pt}
\renewcommand{\footrulewidth}{0pt}

\fancypagestyle{plain}{%
  \fancyhf{}%
  \fancyfoot[C]{\thepage}%
  \renewcommand{\headrulewidth}{0pt}%
}

% --- Strona pusta celowo ---
\newcommand{\TPL@blankpage}{%
  \clearpage%
  \thispagestyle{empty}%
  \vspace*{\fill}%
  \begin{center}%
    \small\textit{Ta strona celowo pozosta{\l}a pusta}%
  \end{center}%
  \vspace*{\fill}%
  \clearpage%
}

% --- Skład strony tytułowej ---
\newcommand{\TPL@maketitlepage}{%
  \thispagestyle{empty}%
  \begin{titlepage}%
    \begin{center}%
      {\fontsize{13pt}{16pt}\selectfont \textbf{POLITECHNIKA {\L}{\'O}DZKA}}\\[0.25em]%
      {\fontsize{11pt}{14pt}\selectfont \TPL@faculty}\\[0.25em]%
      {\fontsize{10pt}{13pt}\selectfont \TPL@department}\\[2.5em]%

      \ifTPL@confidential%
        {\color{red}\textbf{DOKUMENT POUFNY --- EGZEMPLARZ NR \TPL@copynumber}}\\[1.5em]%
      \fi%

      \begin{flushleft}%
        {\fontsize{11pt}{14pt}\selectfont \TPL@authortitle\ \textbf{\TPL@authorname}}\\%
        {\fontsize{10pt}{13pt}\selectfont Nr albumu: \TPL@studentnumber}%
      \end{flushleft}%

      \vspace{2.5em}%
      {\fontsize{15pt}{19pt}\selectfont \textbf{PRACA DYPLOMOWA \MakeUppercase{\TPL@degreename}}}\\[0.8em]%
      {\fontsize{11pt}{14pt}\selectfont na kierunku \textbf{\TPL@fieldofstudy}}\\[2.5em]%

      {\fontsize{16pt}{21pt}\selectfont \textbf{\TPL@thesistitle}}\\[3.5em]%

      \vspace*{\fill}%

      \begin{flushright}%
        \begin{tabular}{ll}%
          \textbf{Promotor:} & \TPL@supervisor \\%
          \ifx\TPL@cosupervisor\@empty\else%
            \textbf{Promotor pomocniczy:} & \TPL@cosupervisor \\%
          \fi%
          \ifx\TPL@partnersupervisor\@empty\else%
            \textbf{Promotor partnerski:} & \TPL@partnersupervisor \\%
          \fi%
        \end{tabular}%
      \end{flushright}%

      \vspace{2.5em}%
      {\fontsize{10pt}{13pt}\selectfont {\L}{\'O}D{\'Z}\ \the\year}%
    \end{center}%
  \end{titlepage}%
}

% --- Automatyczny skład części wstępnej ---
\AtBeginDocument{%
  \TPL@maketitlepage%
  \TPL@blankpage%
  \pagenumbering{roman}%
  \tableofcontents%
  \TPL@blankpage%

  % Streszczenie w języku polskim
  \ifx\TPL@abstract\@empty\else%
    \chapter*{Streszczenie}%
    \addcontentsline{toc}{chapter}{Streszczenie}%
    \TPL@abstract\par%
    \ifx\TPL@keywords\@empty\else%
      \vspace{1.5em}\noindent\textbf{S{\l}owa kluczowe:} \TPL@keywords\par%
    \fi%
    \clearpage%
  \fi%

  % Abstract w języku angielskim
  \ifx\TPL@abstractsecondary\@empty\else%
    \chapter*{Abstract}%
    \addcontentsline{toc}{chapter}{Abstract}%
    \TPL@abstractsecondary\par%
    \ifx\TPL@keywordssecondary\@empty\else%
      \vspace{1.5em}\noindent\textbf{Keywords:} \TPL@keywordssecondary\par%
    \fi%
    \clearpage%
  \fi%

  \TPL@blankpage%
  \pagenumbering{arabic}%
  \setcounter{page}{1}%
}

% --- Automatyczny skład list końcowych ---
\AtEndDocument{%
  \ifx\TPL@symbolslist\@empty\else%
    \chapter*{Wykaz symboli i oznacze{\'n}}%
    \addcontentsline{toc}{chapter}{Wykaz symboli i oznacze{\'n}}%
    \TPL@symbolslist\par%
  \fi%
  \ifx\TPL@abbreviationslist\@empty\else%
    \chapter*{Wykaz u{\.z}ywanych skr{\'o}t{\'o}w}%
    \addcontentsline{toc}{chapter}{Wykaz u{\.z}ywanych skr{\'o}t{\'o}w}%
    \TPL@abbreviationslist\par%
  \fi%
  \ifx\TPL@definitionslist\@empty\else%
    \chapter*{Lista definicji}%
    \addcontentsline{toc}{chapter}{Lista definicji}%
    \TPL@definitionslist\par%
  \fi%
}

\endinput

