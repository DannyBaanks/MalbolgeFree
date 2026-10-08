#include <stdio.h>
#include <stdlib.h>
#include <ctype.h>
#include <string.h>
#include <math.h>
#include <unistd.h>

#define ALLOCATED 1
#define UNALLOCATED 0

#ifdef __GNUC__
static inline
#endif
void exec(int flag[59049], unsigned int **mem, unsigned int init[59049][2] );

#ifdef __GNUC__
static inline
#endif
unsigned int op( unsigned int x, unsigned int y );
void make_init_mem(int id, unsigned int **mem, unsigned int init[59049][2]);

const char xlat1[] =
    "+b(29e*j1VMEKLyC})8&m#~W>qxdRp0wkrUo[D7,XTcA\"lI"
  ".v%{gJh4G\\-=O@5`_3i<?Z';FNQuY]szf$!BS/|t:Pn6^Ha";

const char xlat2[] =
    "5z]&gqtyfr$(we4{WP)H-Zn,[%\\3dL+Q;>U!pJS72FhOA1C"
  "B6v^=I_0/8|jsb9m<.TVac`uY*MK'X~xDl}REokN:#?G\"i@";
  FILE *f;
  FILE *fperror;
int main( int argc, char **argv )
{

  unsigned int **mem;
  int flag[59049];// ブロックが使用済みか否か
  unsigned int init[59050][2]; // 各ブロックの最初2つ分の初期値を記憶
  unsigned int i,ii = 0;
  int x;

  int opt, outf=0;
  char *usage="Usage: malbolge20 [-oh] prog-file\n \
    -o: use file \"info\" for error message\n \
    -h: show this message\n \
";


  while ((opt = getopt(argc, argv, "oh")) != -1) {
    switch (opt){
    case 'o': 
      outf=1;
      break;

    case 'h':
    default:
      fputs(usage, stderr);
      return (1);
    }
  }

  for(i=0;i<59049;i++){// フラグ初期化
    flag[i]=UNALLOCATED;
  }

  if ( outf ) {
    FILE *tmpf;
    if ( ( tmpf = fopen( "info", "w" ) ) != NULL )
    {
      fperror = tmpf;
    }
  } else   fperror = stdout;

  if ( (argc - optind) != 1 )
    {
      fputs(usage, stderr );
      return ( 1 );
    }
  if ( ( f = fopen( argv[optind], "r" ) ) == NULL )
    {
      fputs( "can't open input file\n", stderr );
      return ( 1 );
    }

  mem = (unsigned int **)malloc( sizeof(unsigned int *) * 59049 );
  if ( mem == NULL )
    {
      fclose( f );
      fprintf(fperror, "Error: can't allocate memory\n" );
      fclose(fperror);
      return ( 1 );
    }

  int id=0;
  //第0ブロックのメモリ領域確保
  mem[id] = (unsigned int *)malloc( sizeof(unsigned int) * 59049 );
  if ( mem[id] == NULL )
    {
      fclose( f );
      fprintf(fperror, "Error: can't allocate memory\n" );
      fclose(fperror);
      return ( 1 );
    }
  flag[id]=ALLOCATED;

  //以下で入力プログラムの読み込み
  i=0;
  while ( ( x = getc( f ) ) != EOF )
    {
      if ( isspace( x ) ) continue;
      if ( x < 127 && x > 32 )
	{
	  if ( strchr( "ji*p</vo", xlat1[( x - 33 + ii ) % 94] ) == NULL )
	    {
              fprintf(fperror, "Error: invalid character (ascii=%d) in source file\n",x);
	      free( mem );
	      fclose( f );
	      fclose(fperror);
	      return ( 1 );
	    }
	}else{
        fprintf(fperror, "Error: invalid character (ascii=%d) in source file\n", x);
	free( mem );
	fclose( f );
	fclose(fperror);
      	return ( 1 );
      }
      mem[id][i++] = x;
      ii++;//通しの文字数
      if(i == 59049){//ブロック内の文字数が59049となった場合
	id++;//次のブロックに移る
	if ( id==59049 )//第59049ブロックとなった場合、メモリ不足
	  {
	    fputs( "input file too long\n", stderr );
	    free( mem );
	    fclose( f );
            fclose(fperror);
	    return ( 1 );
	  }
	//次ブロックのメモリ領域を確保
	mem[id] = (unsigned int *)malloc( sizeof(unsigned int) * 59049 );
	if ( mem[id] == NULL )
	  {
	    fclose( f );
            fprintf(fperror, "Error: can't allocate memory\n" );
            fclose(fperror);
	    return ( 1 );
	  }
	flag[id]=ALLOCATED;//第idブロックを使用済みに変更
	i=0;//ブロック内文字数を0に戻す
      }
    }
  fclose( f );//入力の読み込み終了
  //以下は使用中ブロックの余ったメモリの初期化処理
  if(id==0 && i<=1) {   // avoiding errors when null inputs
    fprintf( fperror, "Exited due to an empty input\n" );
    return(1);
  }
  if(i==0){
    mem[id][0] = op( mem[id-1][59048], mem[id-1][59047] );
    mem[id][1] = op( mem[id][0], mem[id-1][59048] );
    i=2;
  }else if(i==1){
    mem[id][1] = op( mem[id][0], mem[id-1][59048] );
    i=2;
  }
  while ( i < 59049 ){
    mem[id][i] = op( mem[id][i - 1], mem[id][i - 2] );
    i++;
  }//初期化処理ここまで

  make_init_mem(id, mem, init);//以降のブロックの遅延初期化を行うための準備

  exec( flag, mem, init );//実行
  free( mem );
  if(outf) fprintf(fperror,"Execution completed.\n");
  fclose(fperror);
  return ( 0 );
}


  /* 各ブロックの遅延初期化を行うための準備をする関数 */
  /* 各ブロックの最初の2ワードを計算し, initに格納 */
void make_init_mem(int id, unsigned int **mem, unsigned int init[59049][2]){
  int i,j;
  int x, y, temp0, temp1;
  int num0[3][3] = {{0, 1, 2}, {0, 1, 1}, {0, 2, 2}, };
  int num1[3][3] = {{1, 0, 0}, {1, 0, 2}, {2, 1, 2}, };

  init[id+1][0]=op( mem[id][59048], mem[id][59047] );
  init[id+1][1]=op( init[id+1][0],  mem[id][59048] );
  id++;
  for(i=id;i<59049;i++){
    temp0=init[id][0];
    temp1=init[id][1];
    init[id+1][0]=0;
    init[id+1][1]=0;
    for(j=0;j<20;j++){
      x = temp0 % 3;
      y = temp1 % 3;
      init[id+1][0] += num0[x][y]*pow(3.0,j);
      init[id+1][1] += num1[x][y]*pow(3.0,j);
      temp0 = temp0/3;
      temp1 = temp1/3;
    }
    id++;
  }
}

#ifdef __GNUC__
static inline
#endif

/* JMPとMOV_Dの時に呼ばれ, その処理を実行する. */
void mem_manage(unsigned int *reg_addr, unsigned int num, int *id, unsigned int **mem, unsigned int init[59049][2], int flag[59049]){
  int new_reg_addr=0;
  int new_id;
  int i;
  new_id=num/59049;
  for(i=0;i<10;i++){
    new_reg_addr += (num % 3)*pow(3.0,i);
    num = num/3;
  }
  *reg_addr=new_reg_addr;

  /* 初期化されていないブロックだった場合、初期化する*/
  if(flag[new_id]==UNALLOCATED){ //すでに初期化済みかチェック
    mem[new_id] = (unsigned int *)malloc( sizeof(unsigned int) * 59049 );
    if ( mem[new_id] == NULL ){
      fclose( f );
      free(mem);
      fprintf(fperror, "Error: can't allocate memory\n");
      fclose(fperror);
      exit ( 1 );
    }
    mem[new_id][0] = init[new_id][0];
    mem[new_id][1] = init[new_id][1];
    i=2;
    while ( i < 59049 ){
      mem[new_id][i] = op( mem[new_id][i-1], mem[new_id][i-2] );
      i++;
    }
    flag[new_id]=ALLOCATED;
  }
  *id=new_id;
}

/* 命令実行後のインクリメント. increment(c, c_id)*/
void increment(unsigned int *reg_addr, int *id, int flag[59049], unsigned int **mem, unsigned int init[59049][2]){
  int i;
  if ( *reg_addr == 59048 ){
    if(*id == 59048){
      *id = 0; *reg_addr = 0;
    }else{
      *id+=1; *reg_addr=0;
      if(flag[*id]==UNALLOCATED){ //すでに初期化済みかチェック
	mem[*id] = (unsigned int *)malloc( sizeof(unsigned int) * 59049 );
	if ( mem[*id] == NULL ){
	  fclose( f );
          fprintf(fperror, "Error: can't allocate memory\n");
          fclose(fperror);
	  exit ( 1 );
	}
	mem[*id][0] = init[*id][0];
	mem[*id][1] = init[*id][1];
	for(i=2; i<59049; i++ ){
	  mem[*id][i] = op( mem[*id][i-1], mem[*id][i-2] );
	}
	flag[*id]=ALLOCATED;
      }
    }
  }else {
    *reg_addr += 1;
  }
}


void exec( int flag[59049], unsigned int **mem, unsigned int init[59049][2] )
{
  unsigned int a = 0, c = 0, d = 0;
  int x;
  int c_id=0, d_id=0;
  for (;;)
    {
      if ( mem[c_id][c] < 33 || mem[c_id][c] > 126 ) {
        fprintf(fperror,"Error: enterring into an infinite loop.\n");
        fclose(fperror);
	exit(1);
	//continue; //　もともとの処理
	}
      switch ( xlat1[( mem[c_id][c] - 33 + (c+c_id*59049) ) % 94] )
	{
	case 'j': //MOV_D
	  mem_manage(&d, mem[d_id][d], &d_id, mem, init, flag);
	  break;
	case 'i': //JMP
	  mem_manage(&c, mem[d_id][d], &c_id, mem, init, flag);
	  break;
	case '*': //ROT
	  a = mem[d_id][d] = mem[d_id][d] / 3 + mem[d_id][d] % 3 * pow(3,19);
	  break;
	case 'p': // OPR
	  a = mem[d_id][d] = op( a, mem[d_id][d] );
	  break;
	case '<'://OUTPUT
	         #if '\n' != 10
	  if ( x == 10 ) putc( '\n', stdout );else
	           #endif
	    putc( a, stdout );
	  break;
	case '/'://INPUT
	  x = getc( stdin );
	         #if '\n' != 10
	  if ( x == '\n' ) a = 10; else
	           #endif
	    if ( x == EOF ) a = 59049 ; else a = x;
	  break;
	case 'v':return;//HALT
	}
      mem[c_id][c] = xlat2[mem[c_id][c] - 33];
      increment(&c, &c_id, flag, mem, init);
      increment(&d, &d_id, flag, mem, init);
    }
}

#ifdef __GNUC__
static inline
#endif

unsigned int op( unsigned int x, unsigned int y )
{
  unsigned int i = 0, j;
    static const unsigned int p9[10] =
      { 1, 9, 81, 729, 6561 ,59049, 531441, 4782969, 43046721, 387420489};
      static const unsigned int o[9][9] =
	{
	  { 4, 3, 3, 1, 0, 0, 1, 0, 0 },
	  { 4, 3, 5, 1, 0, 2, 1, 0, 2 },
	  { 5, 5, 4, 2, 2, 1, 2, 2, 1 },
	  { 4, 3, 3, 1, 0, 0, 7, 6, 6 },
	  { 4, 3, 5, 1, 0, 2, 7, 6, 8 },
	  { 5, 5, 4, 2, 2, 1, 8, 8, 7 },
	  { 7, 6, 6, 7, 6, 6, 4, 3, 3 },
	  { 7, 6, 8, 7, 6, 8, 4, 3, 5 },
	  { 8, 8, 7, 8, 8, 7, 5, 5, 4 },
	};
      for ( j = 0; j < 10 ; j++ )
	i += o[y / p9[j] % 9][x / p9[j] % 9] * p9[j];
      return ( i );
}
