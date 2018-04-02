#ifdef __linux__
	#include <QtCore>
#else
	#include <QtCore/QtCore>
#endif

#include <stdio.h>

int main()
{
	printf("Initialized Qt %s\n", qVersion());
	return 0;
}
