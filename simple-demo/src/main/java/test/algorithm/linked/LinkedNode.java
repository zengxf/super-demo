package test.algorithm.linked;

import lombok.AllArgsConstructor;

/**
 * <br/>
 * Created by ZXFeng on  2021/11/4.
 */
@AllArgsConstructor(staticName = "of")
public class LinkedNode {

    LinkedNode next;
    int value;

    public String toString() {
        return "v: " + value;
    }

}
