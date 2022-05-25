package test.algorithm.linked;

import lombok.extern.slf4j.Slf4j;

/**
 * 递归反转链表
 * <br/>
 * https://labuladong.github.io/algo/2/17/17/
 * <br/>
 * Created by ZXFeng on  2021/11/4.
 */
@Slf4j
public class ReverseLinked {

    public static void main(String[] args) {
        LinkedNode linked = getLinked();
        log.info("linked: [{}]", linkedStr(linked));
        LinkedNode reverse = reverse(linked);
        log.info("reverse-linked: [{}]", linkedStr(reverse));

        log.info("\n\n------------------\n");
        linked = getLinked();
        log.info("linked: [{}]", linkedStr(linked));
        reverse = reverseN(linked, 3);
        log.info("reverse-n-linked: [{}]", linkedStr(reverse));

        log.info("\n\n------------------\n");
        linked = getLinked();
        log.info("linked: [{}]", linkedStr(linked));
        reverse = reverseBetween(linked, 2, 4);
        log.info("reverse-n-linked: [{}]", linkedStr(reverse));
    }


    /*** 反转链表的一部分 */
    static LinkedNode reverseBetween(LinkedNode head, int m, int n) {
        // base case
        if (m == 1) {
            return reverseN(head, n);
        }
        // 前进到反转的起点触发 base case
        head.next = reverseBetween(head.next, m - 1, n - 1);
        return head;
    }

    static LinkedNode successor = null; // 后继节点

    /*** 反转前 N 个节点 */
    // 反转以 head 为起点的 n 个节点，返回新的头结点
    static LinkedNode reverseN(LinkedNode head, int n) {
        if (n == 1) {
            // 记录第 n + 1 个节点
            successor = head.next;
            return head;
        }
        // 以 head.next 为起点，需要反转前 n - 1 个节点
        LinkedNode last = reverseN(head.next, n - 1);
        head.next.next = head;
        // 让反转之后的 head 节点和后面的节点连起来
        head.next = successor;
        return last;
    }

    /*** 反转整个链表 */
    static LinkedNode reverse(LinkedNode head) {
        if (head.next == null)
            return head;
        LinkedNode last = reverse(head.next);
        head.next.next = head; // 这个步骤相当于反转
        head.next = null;
        return last;
    }


    private static String linkedStr(LinkedNode node) {
        StringBuilder sb = new StringBuilder();
        while (node != null) {
            sb.append("[")
                    .append(node.toString())
                    .append("]");
            node = node.next;
            if (node != null) {
                sb.append(" -> ");
            }
        }
        return sb.toString();
    }

    private static LinkedNode getLinked() {
        int size = 5;
        LinkedNode head = null;
        for (int i = size; i >= 1; i--) {
            head = LinkedNode.of(head, i);
        }
        return head;
    }

}
