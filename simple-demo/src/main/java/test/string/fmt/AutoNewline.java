package test.string.fmt;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.Arrays;

/**
 * 自动换行
 * <br/>
 * Created by ZXFeng on 2022/9/28.
 */
public class AutoNewline {

    private static final char[] cnSymbol;
    static String filePath = "D:\\MyData\\note-backup\\未整理\\temp.md";

    static {
        cnSymbol = "，。：；？".toCharArray();
        Arrays.sort(cnSymbol);
    }

    public static void main(String[] args) throws IOException {
        fmtFile();
    }

    static void fmtFile() throws IOException {
        System.out.println("\n--------------------------");
        long st = System.currentTimeMillis();

        Path path = Paths.get(filePath);
        String str = Files.readString(path);
        String newStr = fmtStr(str);
        Files.writeString(path, newStr);

        System.out.println("格式完成，用时（ms）：" + (System.currentTimeMillis() - st));
        System.out.println("--------------------------\n");
    }

    static String fmtStr(String str) {
        char[] arr = str.toCharArray();
        StringBuilder sb = new StringBuilder(arr.length);

        char pre = arr[0];
        sb.append(pre);
        for (int i = 1; i < arr.length; i++) {
            char cur = arr[i];
            boolean added = false;
            if (isSymbol(pre)) {    // 前面可换行的符号
                if (cur != '\r') {  // 现在不是换行，在符号后面加一个换行
                    sb.append("\r\n");
                    sb.append(cur);
                    added = true;
                }
            }
            if (!added) {
                sb.append(cur);
            }
            pre = cur;
        }

        return sb.toString();
    }

    static boolean isSymbol(char c) {
        return Arrays.binarySearch(cnSymbol, c) >= 0;
    }

}
