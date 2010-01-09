/**
 * pyClanSphere bulletin board addons
 * ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
 *
 * Provides helper functions for the bulletin board
 *
 * :copyright: (c) 2010 by the pyClansphere Team, see AUTHORS for more details.
 * :license: BSD, see LICENSE for more details.
 */

var pyCSBulletinBoard = {
    quotePost : function(postid) {
        pyClanSphere.callJSONService('bulletin_board/get_post', {'post_id':postid}, function(p){
           pyClanSphere.insertText('text','[b]' + p.author + '[/b][quote]' + p.text + '[/quote]'); 
        });
    }
}